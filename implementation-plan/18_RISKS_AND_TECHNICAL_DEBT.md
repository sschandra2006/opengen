# 18. RISKS, TECHNICAL DEBT & FAILURE MODE ANALYSIS

> **Document ID:** `OPENGEN-RISK-018`  
> **Author:** Principal Software Architect, Senior Full-Stack Engineer, AI Infrastructure Engineer  
> **Project:** OpenGen Framework  
> **Date:** November 2026  
> **Assessment Scope:** Technical, Security, Financial, and Operational Risk  

---

## 1. Executive Summary

This document performs an exhaustive pre-implementation risk audit and technical debt assessment for OpenGen.

Every identified risk is categorized by **Severity** (Critical, High, Medium, Low) and **Probability** (High, Medium, Low), with concrete architectural mitigations designed directly into the framework.

---

## 2. Master Risk & Mitigation Matrix

| Risk ID | Risk Domain & Description | Severity | Probability | Impact | Mitigation Strategy |
|---|---|---|---|---|---|
| **RSK-01** | **Test Harness State Contamination:** Legacy tests share global `.ai-document-memory/` state, causing cross-test assertion failures on repeated runs. | **Critical** | **High** | Broken CI/CD; false negative test runs. | Implement session/per-test `tmp_path` fixture in `conftest.py` redirecting cache and DB to ephemeral folders. |
| **RSK-02** | **Zip & Decompression Bombs:** Attackers upload maliciously compressed DOCX/PPTX files that expand to tens of gigabytes, exhausting host disk and memory. | **Critical** | **Medium** | Host server denial of service / crash. | Enforce decompression ratio checks (max 10:1) and absolute uncompressed size limits (max 100 MB) via `SafePackageExtractor`. |
| **RSK-03** | **XML Entity Expansion (Billion Laughs):** Recursive entity definitions in DOCX/PPTX XML packages consume exponential CPU and RAM. | **Critical** | **Medium** | Complete CPU hang in web workers. | Mandatory use of `defusedxml` across all Office OpenXML package parsing. |
| **RSK-04** | **API Key Leakage in Logs:** Provider API keys (`sk-`, `AIza`, `together_`) printed in cleartext during exception traces. | **Critical** | **Medium** | Severe credential compromise; unauthorized cloud billing. | Type keys as `pydantic.SecretStr`; install `LogSanitizerFilter` regex scrubber on all logging sinks. |
| **RSK-05** | **Path Traversal Escape (`../`):** Malicious template URIs attempting to read sensitive host files or escape the workspace. | **Critical** | **Low** | Unauthorized host file disclosure. | Enforce strict `pathlib.Path.resolve().is_relative_to(ALLOWED_WORKSPACE_ROOT)` checks on every file operation. |
| **RSK-06** | **PowerPoint Image Flattening Trap:** Generating presentation cards as static raster images destroys native editability in Microsoft PowerPoint. | **High** | **High** | Rejection by corporate users; failure of core value proposition. | Strictly mandate that all shapes, text boxes, and charts are built as native OOXML objects via `python-pptx`. |
| **RSK-07** | **Physical Notebook Paper Misalignment (Engine D):** Home printers experience slight physical paper feed slip, causing ink to drift off ruled notebook lines. | **High** | **Medium** | Synthetic handwriting appears misaligned with physical lines. | Implement printer calibration test page and configurable sub-millimeter baseline offset parameters (`pitch_offset_mm`, `top_margin_offset_mm`). |
| **RSK-08** | **Headless LibreOffice Zombie Processes:** Unresponsive LibreOffice headless conversion processes hang indefinitely, accumulating memory. | **High** | **Medium** | Memory leakage; eventual worker starvation. | Enforce strict 60-second timeouts on all conversion subprocesses; clean up child process trees on timeout. |
| **RSK-09** | **Provider Rate Limits (429) & Outages:** Cloud AI providers experience transient rate limits or 503 service disruptions during high-volume generation. | **High** | **High** | Job failures; interrupted user workflows. | Configure `LiteLLM` automatic 3-tier fallback chains (Primary -> Secondary -> Local Ollama) with exponential backoff. |
| **RSK-10** | **Large Document Memory Bloat (>100 pages):** Loading massive 200-page reference PDFs or parsing thousands of table rows exhausts RAM. | **Medium** | **Medium** | Process killed by OOM killer. | Implement chunked page-by-page streaming extraction via PyMuPDF; enforce 500-page caps. |
| **RSK-11** | **Heavy Dependency Bloat (Docling & PyTorch):** Defaulting to Docling pulls ~2 GB of PyTorch weights, causing 10-minute installation times and high Docker image sizes. | **Medium** | **High** | Poor developer experience; slow container cold starts. | Isolate Docling in optional extra: `pip install opengen[docling]`. Keep PyMuPDF as the lightweight, zero-token default. |
| **RSK-12** | **FastAPI Background Task Loss:** Ephemeral background tasks inside web workers are permanently lost if the uvicorn process restarts. | **High** | **Medium** | Unrecoverable in-flight jobs. | Migrate from `BackgroundTasks` to persistent `SqliteHuey` queue. |
| **RSK-13** | **Anti-Hallucination False Positives:** Overly strict mapping rules block legitimate user fields, causing unnecessary user clarification interruptions. | **Medium** | **Medium** | Degraded user experience. | Support Levenshtein fuzzy synonym matching and allow user-override instructions (`instruction: "Assume student is enrolled"`). |
| **RSK-14** | **Windows COM Dependency in Production:** Converting DOCX to PDF via Windows Word COM (`win32com.client`) fails when deployed on Linux Docker containers. | **High** | **High** | PDF rendering failure in cloud/Linux environments. | Multi-tier rendering strategy: Windows COM on Windows desktop -> Headless LibreOffice on Linux -> WeasyPrint for direct reports. |

---

## 3. Deep Forensic Investigation of Critical Failure Modes

### 3.1 Failure Mode 1: The Test Contamination Bug
- **Investigation:** During our live audit, running `python -m pytest -v` resulted in 2 failed tests:
  1. `test_cache_invalidation_on_file_change`: Expected `storage.get_template_profile(hash_v2)` to return `None`, but it returned cached data from a previous test run.
  2. `test_duplicate_detection`: Expected `is_duplicate == True`, but returned `False` due to stale file record paths.
- **Root Cause Analysis:** The current codebase initializes a global SQLite storage object (`storage = SQLiteStorage()`) that hardcodes `.ai-document-memory/metadata.db`. When tests run, they insert rows into this shared production database. Consecutive test runs encounter leftover state.
- **Permanent Solution:**
  1. Refactor `storage.py` into `DiskCacheManager` which reads its path from `settings.CACHE_DIR`.
  2. Implement `conftest.py` with an `autouse=True` fixture that sets `OPENGEN_CACHE_DIR` to a fresh temporary directory per test run.
  3. When tests finish, the temporary directory is automatically purged.

---

### 3.2 Failure Mode 2: The PowerPoint Editability Trap
- **Investigation:** Commercial web-native generators (Gamma, Pitch, Canva) export to PowerPoint by rendering CSS elements or HTML canvases into static PNG images or unlinked detached shapes.
- **Business Consequence:** When an executive or enterprise team receives the deck, they cannot change a typo, edit a chart number in Excel, or re-apply their company's Slide Master template.
- **OpenGen Defense:**
  - OpenGen completely bypasses web-to-PPTX conversion.
  - All slides are constructed directly at the OOXML level using `python-pptx`.
  - Every card is a native PowerPoint shape (`MSO_SHAPE.ROUNDED_RECTANGLE`).
  - Every chart is a native Microsoft Excel chart stream (`XL_CHART_TYPE.COLUMN_CLUSTERED`).
  - Output files are guaranteed to be 100% native and editable.

---

### 3.3 Failure Mode 3: Physical Printing Line Slip in Engine D
- **Investigation:** Standard home inkjet and laser printers feed paper via mechanical rubber rollers. A single sheet of notebook paper can experience a $\pm 0.5\text{ mm}$ mechanical feed variance.
- **Forensic Consequence:** If the printed ink baseline drifts across 25 lines of a page, by line 20 the handwriting may sit slightly above or below the physical blue ruled line, revealing that it was printed rather than hand-written.
- **OpenGen Defense:**
  1. **Sub-Millimeter Calibration Calibration Sheet:** OpenGen provides a test alignment sheet (`opengen handwriting calibrate`) that prints three tick marks at exact millimeter intervals. The user measures the printed marks with a ruler and inputs their printer's feed offset.
  2. **Mean-Reverting Baseline Tracking:** Engine D's Brownian drift algorithm includes an active spring force:
     $$y_{i+1} = y_i + \Delta y_i - k(y_i - y_{\text{line\_baseline}})$$
     This guarantees that even with human micro-jitter, the ink mathematically never drifts away from the physical notebook line.

---

## 4. Technical Debt Paydown Roadmap

| Technical Debt Item | Current Codebase Location | Paydown Action | Phase Target |
|---|---|---|---|
| **Directory Side-Effects** | `app/config.py` (lines 55-65) | Move `mkdir` calls into FastAPI lifespan and CLI init routines. | Phase 1 |
| **Low-Level urllib Calls** | `app/modules/token_optimization/ai_router.py` | Replace with `LiteLLM` multi-provider bridge. | Phase 2 |
| **Dual Storage (SQLite + JSON)** | `app/modules/memory_cache/storage.py` | Unify under `diskcache.FanoutCache`. | Phase 1 |
| **FastAPI BackgroundTasks** | `app/web/routes.py` | Migrate to persistent `SqliteHuey` queue. | Phase 1 |
| **Word COM Windows Coupling** | `app/modules/visual_validation/renderer.py` | Standardize WeasyPrint and headless LibreOffice. | Phase 3 |
| **Unversioned API Routes** | `app/web/routes.py` | Version under `/api/v1/`. | Phase 7 |

---
*End of Report 18.*
