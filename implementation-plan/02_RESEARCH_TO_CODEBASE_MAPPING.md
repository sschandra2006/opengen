# 02. RESEARCH-TO-CODEBASE MAPPING & EVALUATION

> **Document ID:** `OPENGEN-MAPPING-002`  
> **Author:** Principal Software Architect, Senior Full-Stack Engineer, AI Infrastructure Engineer  
> **Project:** OpenGen Framework Transformation  
> **Date:** November 2026  
> **Reference Document:** `OPENGEN_COMPREHENSIVE_RESEARCH_REPORT.md`  

---

## 1. Executive Overview

The research document (`OPENGEN_COMPREHENSIVE_RESEARCH_REPORT.md`) defines an ambitious, industry-grade technical vision for an open-source generative framework spanning:
- **Engine A:** Document Generation (DOCX, PDF, Templates, Reference Merging)
- **Engine B:** Presentation Generation (PPTX, Dynamic Geometry, Native Charts)
- **Engine C:** Image Generation (FLUX.1 Schnell, DALL-E, Recraft Vectors)
- **Engine D:** Pure Realistic Handwriting Generation (Anti-Detection Physics, Physical Notebook Printing)
- **4 Primary Interfaces:** Python SDK, FastAPI REST, FastMCP Server, Typer CLI
- **Underlying Pillars:** BYOK Multi-Provider (`LiteLLM`), Zero-Daemon Queue (`Huey`), 3-Tier Caching (`diskcache`), and Token-Efficient Engineering.

This report systematically maps every recommendation from the 11 research reports against the existing codebase (`app/`), evaluates its architectural appropriateness, identifies where the codebase aligns with the research, and flags where adjustments are required.

---

## 2. Research Report to Codebase Mapping Matrix

| Research Section | Research Recommendation | Current Codebase Implementation | Evaluation & Implementation Decision |
|---|---|---|---|
| **Report 1: Product Analysis** | Editable DOCX output with native OOXML tables, headers, footers | Implemented in `app/modules/document_generation/docx_populator.py` & `table_builder.py` | **100% Appropriate.** Retain existing OOXML logic; integrate `docxtpl` for advanced Jinja2 table looping. |
| **Report 1: Product Analysis** | Slide Master layout preservation & native Excel-backed charts (vs Gamma image flattening) | **Missing.** Codebase has zero PPTX generation files. | **Critical Need.** Build `opengen.engines.presentation` using `python-pptx` with geometry solvers. |
| **Report 1: Product Analysis** | Native Vector SVG generation (Recraft / Ideogram) & FLUX.1 raster | **Missing.** Codebase has zero image generation capabilities. | **High Priority.** Implement `opengen.engines.image` with Together AI (FLUX) and Recraft API. |
| **Report 2: Open-Source Repositories** | `python-docx` (MIT) & `docxtpl` (LGPLv2.1) for Word manipulation | `python-docx` is actively used; `docxtpl` is in `requirements.txt` but not yet called in code. | **Adopt.** Use `python-docx` for low-level structural assembly; use `docxtpl` for Jinja2 template merging behind an isolated interface. |
| **Report 2: Open-Source Repositories** | `python-pptx` (MIT) for presentation generation | Absent from `requirements.txt` and source code. | **Mandatory Add.** Add `python-pptx>=1.0.2` for Engine B. |
| **Report 2: Open-Source Repositories** | `WeasyPrint` (BSD-3-Clause) for deterministic HTML-to-PDF rendering | Not installed. Codebase relies on Windows Word COM or LibreOffice headless via `renderer.py`. | **Adopt as Primary Cross-Platform PDF Engine.** Retain LibreOffice/Word COM as DOCX-to-PDF converters, but use WeasyPrint for direct HTML/CSS report generation. |
| **Report 2: Open-Source Repositories** | `Docling` (MIT / Apache-2.0) vs `PyMuPDF` | Both are installed; `PyMuPDF` is the primary fast parser; `Docling` is a fallback stub in `docling_extractor.py`. | **Refine.** Keep PyMuPDF as default zero-token local parser. Isolate Docling as an optional extra (`opengen[docling]`) due to heavy PyTorch weights. |
| **Report 2: Open-Source Repositories** | `LiteLLM` (MIT) for universal AI provider translation | Absent. Codebase uses `google-generativeai` and raw `urllib` calls in `ai_router.py`. | **Mandatory Replacement.** Replace `ai_router.py` with `LiteLLM` to immediately unlock OpenAI, Claude, Gemini, Together, and Ollama under one API. |
| **Report 2: Open-Source Repositories** | `FastMCP` (MIT) for Model Context Protocol | Absent from codebase. | **Mandatory Add.** Add `mcp[cli]>=1.2.0` to build native MCP server for Claude and Antigravity. |
| **Report 2: Open-Source Repositories** | `Huey` (MIT) via `SqliteHuey` for zero-daemon async tasks | Codebase uses `fastapi.BackgroundTasks` inside web workers. | **Mandatory Replacement.** Implement `SqliteHuey` for reliable background job execution that survives worker restarts. |
| **Report 2: Open-Source Repositories** | `diskcache` (Apache 2.0) for L2 cache | Codebase implements custom SQLite queries in `storage.py`. | **Adopt.** Replace ad-hoc SQLite JSON text caches with `diskcache.FanoutCache` with automatic LRU and TTL eviction. |
| **Report 4: Provider Matrix** | Route cheap models (`gemini-2.5-flash`, `gpt-4o-mini`, `qwen3:8b`) for structured JSON planning | Hardcoded in `ai_router.py` (`qwen3:8b` and `gemini-2.5-flash`). | **Expand.** Generalize model routing through a capability-based registry (Task Type -> Best Provider/Model). |
| **Report 4: Provider Matrix** | Provider-side Prompt Caching (Anthropic 90% discount, Gemini context cache) | Not implemented. System prompts are concatenated on every request. | **Implement.** Pin system prompts and schemas to trigger provider-side prefix caching. |
| **Report 5: System Architecture** | `src/opengen` modular layout with Ports & Adapters | Codebase uses flat `app/` directory with mixed concerns. | **Execute Migration.** Migrate `app/` to `src/opengen/` following modern Python packaging standards (`pyproject.toml`). |
| **Report 6: Workflow Design** | 4-Stage Document Generation Pipeline (Validation, Extraction, Mapping, Visual Loop) | Fully implemented in `app/modules/pipeline.py`! | **100% Aligned.** The existing 7-module document workflow mirrors the research pipeline. Retain and formalize as `DocumentEngine`. |
| **Report 6: Workflow Design** | Presentation Storytelling Planner & Coordinate Geometry Solver | Absent from codebase. | **Implement from scratch** following Report 6.2 specifications. |
| **Report 7: Token Optimization** | "Never pay an LLM to do what deterministic code does for free" | Codebase strongly respects this! Regex, OCR, layout heuristics, and tables use 0 tokens. | **Preserve & Benchmark.** Keep deterministic extractors and document builders as first-class citizens. |
| **Report 8: Security Plan** | Path traversal guards, `pydantic.SecretStr`, `defusedxml` | Basic path sanitization in `validator.py`, but lacks strict root containment and `defusedxml`. | **Harden.** Implement `opengen.security.path_guard` and integrate `defusedxml` on all DOCX/PPTX unzipping. |
| **Report 11: Engine D (Handwriting)** | Anti-detection handwriting, multi-glyph alternates, physical notebook paper transparent printing | Absent from codebase. | **Implement Engine D.** Build `opengen.engines.handwriting` supporting transparent PDF mode for direct printer feeding. |

---

## 3. Critical Technical Evaluations & Codebase Reality Checks

While the research report provides an extraordinary technical foundation, a responsible architect must critically evaluate every recommendation against real-world execution constraints.

### 3.1 Evaluation 1: PyMuPDF License Risk vs Docling Heavyweight Reality
- **Research Note:** Report 2 mentions PyMuPDF's AGPLv3 license risk and recommends Docling (MIT/Apache 2.0).
- **Codebase Reality:** The existing codebase relies extensively on `fitz` (`PyMuPDF`) in `pdf_analyzer.py`, `pymupdf_extractor.py`, `inspector.py`, and `pdf_reconstructor.py`. PyMuPDF runs in under 15ms per page on pure CPU with minimal memory. Conversely, `Docling` downloads ~2 GB of PyTorch weights and takes 3-8 seconds per page on CPU.
- **Architectural Resolution:**
  - In OpenGen Core, provide an abstracted document parser interface (`IDocumentParser`).
  - For open-source personal/developer use, PyMuPDF can be used or packaged under commercial licensing or replaced with `pypdf` + `pdfplumber` (MIT/BSD).
  - Make `Docling` an optional plugin: `pip install opengen[docling]`.
  - Provide a pure-permissive fallback parser (`pypdf` + `pdfminer.six`) so users with strict AGPL compliance policies can run without PyMuPDF.

### 3.2 Evaluation 2: WeasyPrint vs Microsoft Word COM / LibreOffice
- **Research Note:** Recommends WeasyPrint (BSD-3-Clause) as the primary PDF renderer.
- **Codebase Reality:** The codebase currently converts `.docx` to `.pdf` via Windows Word COM (`win32com.client`) or headless LibreOffice (`soffice --headless --convert-to pdf`). WeasyPrint converts *HTML/CSS* to PDF, not `.docx` to PDF!
- **Architectural Resolution:**
  - Acknowledge the distinction between **Direct PDF Report Generation** (HTML+CSS -> WeasyPrint -> PDF) and **Word Document to PDF Conversion** (`.docx` -> PDF).
  - OpenGen will support **both**:
    1. For `.docx` templates, conversion to PDF requires headless LibreOffice or Windows Word COM.
    2. For fresh document generation from markdown/JSON, OpenGen introduces a direct WeasyPrint pipeline: Content JSON -> Jinja2 HTML -> WeasyPrint -> Pixel-Perfect PDF (zero Office dependency).

### 3.3 Evaluation 3: `docxtpl` (LGPLv2.1) Isolation
- **Research Note:** Recommends `docxtpl` for Jinja2 template merging.
- **Licensing Constraint:** `docxtpl` is licensed under LGPLv2.1. While LGPL permits dynamic linking, corporate users often require strict isolation.
- **Architectural Resolution:**
  - Wrap all `docxtpl` calls inside `opengen.engines.document.template.DocxTplEngine`.
  - Keep `docxtpl` as an independent dependency dynamically imported at runtime.
  - Preserve the existing `DocxPopulator` which uses pure `python-docx` (MIT) for direct placeholder replacement. Users can choose either the pure MIT populator or the rich Jinja2 `docxtpl` engine.

### 3.4 Evaluation 4: Local Zero-Daemon Queue (Huey vs Celery)
- **Research Note:** Recommends `SqliteHuey` to eliminate Redis/RabbitMQ dependencies for self-hosters.
- **Architectural Validation:** This is a **10/10 recommendation**. The existing codebase runs synchronous jobs inside `fastapi.BackgroundTasks`, which clutters memory and fails on restarts. Adopting `SqliteHuey` requires zero external processes while delivering persistence, automatic retries, and clean worker separation. Migrating to Redis in enterprise clusters requires changing only the configuration URI.

---

## 4. Bridge Strategy: From Prototype to Target OpenGen

```
+-------------------------------------------------------------------------------+
|                             EXISTING PROTOTYPE                                |
|  FastAPI + SQLite + PyMuPDF + python-docx + Hardcoded Gemini/Ollama (app/)    |
+-------------------------------------------------------------------------------+
                                       |
                   MIGRATION & REFACTORING BRIDGE
                                       |
                                       v
+-------------------------------------------------------------------------------+
|                               OPENGEN TARGET                                  |
|                                                                               |
|  [INGRESS]     Python SDK      FastAPI REST      FastMCP Server      CLI      |
|                                                                               |
|  [ENGINES]     Engine A          Engine B          Engine C       Engine D    |
|                (Document)     (Presentation)       (Image)      (Handwriting) |
|                * docx_populator * Layout Solver   * FLUX.1      * Glyph Bank  |
|                * table_builder  * Native Charts   * DALL-E 3    * Jitter/Ink  |
|                * pdf_reconstr.  * python-pptx     * Recraft SVG * Transparent |
|                                                                               |
|  [CORE]        ProviderManager    SqliteHuey       diskcache     PathGuard    |
|                (LiteLLM)         (Async Queue)    (L2 Cache)    (Security)    |
+-------------------------------------------------------------------------------+
```

### Transformation Principles:
1. **Never throw away tested code:** The ~2,500 lines of document generation, table construction, and visual validation code currently in `app/modules/` represent significant testing and intellectual property. They must be ported into `opengen.engines.document`.
2. **Standardize all external calls:** All AI model interactions must route through the new `ProviderManager`.
3. **Decouple web UI from core engine:** The core engines must have zero knowledge of FastAPI, HTTP requests, or browser cookies. They receive validated domain input models and return generation artifacts.

---
*End of Report 02.*
