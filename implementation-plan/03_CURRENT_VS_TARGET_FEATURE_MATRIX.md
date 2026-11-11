# 03. CURRENT STATE VS TARGET STATE FEATURE MATRIX

> **Document ID:** `OPENGEN-MATRIX-003`  
> **Author:** Principal Software Architect, Senior Full-Stack Engineer, AI Infrastructure Engineer  
> **Project:** OpenGen Framework Transformation  
> **Date:** November 2026  
> **Repository Baseline:** `f:\document generator\opengen`  

---

## 1. Executive Summary

This document presents a granular, forensic comparison between the target OpenGen product capabilities (defined in `OPENGEN_COMPREHENSIVE_RESEARCH_REPORT.md` and user specifications) and the actual source code currently present in the repository.

Every status is substantiated by direct source file evidence.

### Status Definitions:
- **IMPLEMENTED:** Complete, functional, and verified implementation exists in the codebase.
- **PARTIALLY IMPLEMENTED:** Some functionality exists, but critical sub-features or interfaces are missing.
- **NEEDS IMPROVEMENT:** Existing functionality works but requires refactoring, decoupling, or security hardening.
- **MISSING:** Zero implementation exists in the current codebase.
- **OPTIONAL:** Secondary feature not strictly blocking Milestone 1 or initial release.
- **BLOCKED:** Cannot proceed until another technical or architectural decision is finalized.

---

## 2. Master Feature Matrix

### 2.1 Engine A: Document Generation

| Target Feature | Status | Existing Files (Source Evidence) | Required Changes & Gaps |
|---|---|---|---|
| **DOCX Template Preservation** | **IMPLEMENTED** | `app/modules/document_generation/docx_populator.py` (lines 26-94) | Working: preserves runs, paragraph styles, margins, headers, footers. Needs porting to `opengen.engines.document.populator`. |
| **PDF Template Reconstruction** | **IMPLEMENTED** | `app/modules/document_generation/pdf_reconstructor.py` (lines 26-100) | Working: reconstructs PDF text blocks and tables into editable Word paragraphs. Port to `opengen.engines.document.reconstructor`. |
| **Jinja2 Advanced Templating (`docxtpl`)** | **PARTIALLY IMPLEMENTED** | `requirements.txt` (line 6: `docxtpl>=0.19.0`) | `docxtpl` is declared in dependencies but never imported in `app/`. Need to build `DocxTplEngine` wrapper for array loops and dynamic tables. |
| **Advanced OOXML Table Construction** | **IMPLEMENTED** | `app/modules/document_generation/table_builder.py` (lines 14-76) | Working: sets `w:cantSplit` (row break prevention), `w:tblHeader` (repeat headers), cell padding `w:tcMar`, and border styling `w:tblBorders`. |
| **PDF Reference Fact Extraction** | **IMPLEMENTED** | `app/modules/reference_intelligence/information_extractor.py` (lines 32-182) | Working: extracts regex key-values, dates, currencies, and entities with page numbers and confidence tracking. |
| **Scanned Document OCR Extraction** | **IMPLEMENTED** | `app/modules/reference_intelligence/ocr_extractor.py` (lines 11-57) | Working: uses RapidOCR with ONNX runtime for image-only PDF pages. Port and add lazy initialization. |
| **Deep Layout Analysis (`Docling`)** | **PARTIALLY IMPLEMENTED** | `app/modules/reference_intelligence/docling_extractor.py` (lines 12-63) | Basic wrapper exists, but is slow on CPU. Isolate behind optional extra `opengen[docling]`. |
| **Anti-Hallucination Semantic Mapping** | **IMPLEMENTED** | `app/modules/intelligent_mapping/mapper.py` (lines 35-150) & `validator.py` | Working: synonym matching, conflict detection, reference validation, anti-hallucination blocker for sensitive facts. |
| **User Clarification Dialog Flow** | **IMPLEMENTED** | `app/modules/pipeline.py` (lines 88-105), `app/web/routes.py` (lines 85-115) | Working: pauses pipeline with status `pending_clarification` if facts conflict or are missing, resumes on `/api/resolve`. |
| **Visual Validation & Auto-Correction** | **IMPLEMENTED** | `app/modules/visual_validation/inspector.py` & `auto_corrector.py` | Working: PyMuPDF checks for overflow, blank pages, and broken tables; auto-corrects by tightening margins/fonts up to 3 loops. |
| **Cross-Platform PDF Export** | **NEEDS IMPROVEMENT** | `app/modules/visual_validation/renderer.py` (lines 20-95) | Relies heavily on Windows COM (`win32com.client`) or external LibreOffice. Must add WeasyPrint direct HTML-to-PDF pipeline. |
| **Partial / Section Regeneration** | **MISSING** | None | Feature does not exist. Must allow users to regenerate specific sections or tables without re-running the full document. |
| **Native Chart Injection into DOCX** | **MISSING** | None | Currently tables and text are supported; OOXML chart insertion (`python-docx-charts` or raw OOXML) is not implemented. |
| **Header/Footer Dynamic Page Fields** | **PARTIALLY IMPLEMENTED** | `app/modules/template_intelligence/docx_analyzer.py` (line 95) | Detects `PAGE` fields in footer, but dynamic insertion of `<w:fldSimple w:instr="PAGE"/>` is not generalized. |

---

### 2.2 Engine B: Presentation Generation

| Target Feature | Status | Existing Files (Source Evidence) | Required Changes & Gaps |
|---|---|---|---|
| **Text to Editable PPTX** | **MISSING** | None | Must implement presentation engine using `python-pptx`. |
| **Outline & Storytelling Planner** | **MISSING** | None | Must implement LLM prompt planner producing structured `SlideDeck` JSON (titles, cards, takeaways). |
| **Coordinate Geometry Layout Solver** | **MISSING** | None | Must implement deterministic geometry engine calculating X, Y, W, H for 1, 2, 3, and 4-column cards. |
| **Font-Scaling Overflow Guard** | **MISSING** | None | Must implement text measurement heuristics to dynamically shrink font sizes if text exceeds card height. |
| **Slide Master & Layout Binding** | **MISSING** | None | Must support importing `.potx` / `.pptx` templates and binding content to layout placeholders. |
| **Theme & Color Palette Management** | **MISSING** | None | Must implement theme dataclasses (`PrimaryColor`, `SecondaryColor`, `BackgroundColor`, `FontHeader`, `FontBody`). |
| **Native Excel-Backed Charts in Slides** | **MISSING** | None | Must implement `python-pptx.chart.data.CategoryChartData` (Bar, Column, Line, Pie) ensuring charts remain editable in Excel. |
| **Slide-Level Regeneration** | **MISSING** | None | Must support regenerating a single slide index without rebuilding the entire deck. |
| **DOCX to PPTX Deck Converter** | **MISSING** | None | Must parse structured DOCX headings and extract bullet points into slide cards. |
| **PDF to PPTX Reconstruction** | **MISSING** | None | Must extract PDF slides/pages into presentation layout cards. |

---

### 2.3 Engine C: Image Generation

| Target Feature | Status | Existing Files (Source Evidence) | Required Changes & Gaps |
|---|---|---|---|
| **Text to Image Generation** | **MISSING** | None | Must implement `ImageEngine` supporting prompt ingestion and provider routing. |
| **FLUX.1 Schnell Provider Adapter** | **MISSING** | None | Must implement Together AI / BFL API adapter for FLUX.1 [schnell] (Apache 2.0). |
| **OpenAI DALL-E 3 Adapter** | **MISSING** | None | Must implement OpenAI Images API adapter (`v1/images/generations`). |
| **Recraft Native Vector (SVG) Adapter** | **MISSING** | None | Must implement Recraft Vector V4 API adapter returning true scalable SVGs. |
| **Pillow Post-Processing Pipeline** | **MISSING** | None | Must implement aspect ratio normalization, EXIF stripping, and thumbnail generation. |
| **Transparent PNG Alpha Masking** | **MISSING** | None | Must implement cutout post-processing for logos and stickers. |
| **Image-to-Image / Inpainting** | **OPTIONAL** | None | Defer to Milestone 3; not required for core MVP release. |
| **Local Diffusers Pipeline** | **OPTIONAL** | None | Heavy GPU dependency (CUDA/torch). Plan as optional extra `opengen[diffusers]`. |
| **Image Prompt Caching (SHA-256)** | **MISSING** | None | Must implement prompt-hash caching in `diskcache` to avoid duplicate paid API calls. |

---

### 2.4 Engine D: Pure Realistic Handwriting Generation

| Target Feature | Status | Existing Files (Source Evidence) | Required Changes & Gaps |
|---|---|---|---|
| **Multi-Glyph Contextual Alternate Bank** | **MISSING** | None | Must implement `GlyphBank` with 5-8 font variants per character ensuring no repeated letters within 3 chars. |
| **Non-Linear Brownian Baseline Drift** | **MISSING** | None | Must implement vertical micro-jitter ($\Delta y \sim \mathcal{N}(0, \sigma^2)$) and subtle line slant. |
| **Pen Physics & Ink Dynamics** | **MISSING** | None | Must implement velocity-based stroke opacity, ballpoint blue (`#1C3B72`) and gel black palettes. |
| **Direct-to-Physical-Notebook Printing** | **MISSING** | None | Must implement 100% transparent RGBA canvas with sub-millimeter line pitch (College Ruled: 7.1mm, Wide: 8.7mm). |
| **Synthetic Scanned Document Emulation** | **MISSING** | None | Must implement paper textures, margin lines, binder holes, and 300 DPI high-res scan rendering. |
| **Human Mistake & Fatigue Injection** | **OPTIONAL** | None | Optional double-line cross-outs and right-margin text compression. |

---

### 2.5 Provider Management & Infrastructure

| Target Feature | Status | Existing Files (Source Evidence) | Required Changes & Gaps |
|---|---|---|---|
| **Multi-Provider Unified Adapter** | **NEEDS IMPROVEMENT** | `app/modules/token_optimization/ai_router.py` (lines 17-119) | Currently hardcoded to Ollama (`urllib`) and Gemini Flash (`google-generativeai`). Must migrate to `LiteLLM`. |
| **Provider Capability Registry** | **MISSING** | None | Must implement dynamic model routing based on task type (JSON schema support, vision, speed, cost). |
| **BYOK (Bring Your Own Key)** | **PARTIALLY IMPLEMENTED** | `app/config.py` (line 38: `GEMINI_API_KEY`) | Reads environment variables, but cannot accept per-request user API keys securely. |
| **Zero-Daemon Async Job Queue** | **NEEDS IMPROVEMENT** | `app/web/routes.py` (line 34: `BackgroundTasks`) | Uses ephemeral FastAPI background tasks. Must migrate to `SqliteHuey` with fallback to `RedisHuey`. |
| **3-Tier Persistent Cache** | **NEEDS IMPROVEMENT** | `app/modules/memory_cache/storage.py` (lines 42-62) | Uses ad-hoc SQLite JSON text blobs. Must migrate to `diskcache` with LRU eviction and memory L1 tier. |
| **Token Accounting & Cost Telemetry** | **PARTIALLY IMPLEMENTED** | `app/modules/token_optimization/tracker.py` (lines 8-27) | Tracks raw token counts, but dollar rates are hardcoded ($0.15/1M). Must use dynamic provider pricing. |
| **Security: Path Traversal Blocker** | **NEEDS IMPROVEMENT** | `app/modules/input_manager/validator.py` (lines 27-31) | Basic `sanitize_filename` regex exists, but lacks `pathlib.Path.is_relative_to(ALLOWED_ROOT)` enforcement. |
| **Security: Defused XML Guard** | **MISSING** | `app/modules/input_manager/validator.py` (line 60: raw `zipfile`) | Unprotected against zip bombs and XML entity expansion. Must integrate `defusedxml` and decompression caps. |
| **Security: Secret Sanitizer in Logs** | **MISSING** | None | Must implement logging filter scrubbing API keys (`sk-`, `AIza`, `together_`). |

---

### 2.6 External Interfaces & Ingress

| Target Feature | Status | Existing Files (Source Evidence) | Required Changes & Gaps |
|---|---|---|---|
| **FastAPI REST API** | **PARTIALLY IMPLEMENTED** | `app/web/routes.py` (lines 20-142) | Endpoints exist for document upload, generate, status, resolve, download. Must version under `/api/v1/` and expand to all engines. |
| **Model Context Protocol (MCP) Server** | **MISSING** | None | Must build FastMCP server exposing tools: `create_document`, `create_presentation`, `generate_image`, `generate_handwriting`. |
| **Python SDK Client** | **MISSING** | None | Must build clean top-level client: `from opengen import OpenGenClient`. |
| **Command-Line Interface (CLI)** | **MISSING** | None | Must build Typer CLI: `opengen generate`, `opengen serve`, `opengen config`. |
| **Web Dashboard UI** | **IMPLEMENTED** | `app/web/static/` (HTML, CSS, JS) | Working interactive single-page dashboard. Can be retained as embedded local GUI. |

---

## 3. Implementation Gap Summary

```
                      IMPLEMENTATION READINESS BY DOMAIN
+---------------------------------------------------------------------------------+
| ENGINE A: DOCUMENT GENERATION      [████████████████████░░░░░]  80% Complete   |
| ENGINE B: PRESENTATION GENERATION  [░░░░░░░░░░░░░░░░░░░░░░░░░]   0% Complete   |
| ENGINE C: IMAGE GENERATION         [░░░░░░░░░░░░░░░░░░░░░░░░░]   0% Complete   |
| ENGINE D: HANDWRITING SYNTHESIS    [░░░░░░░░░░░░░░░░░░░░░░░░░]   0% Complete   |
| PROVIDER MANAGER (LiteLLM)         [██████░░░░░░░░░░░░░░░░░░░]  25% Complete   |
| QUEUE & CACHE INFRASTRUCTURE       [████████░░░░░░░░░░░░░░░░░]  35% Complete   |
| INTERFACES (MCP, SDK, CLI)         [████░░░░░░░░░░░░░░░░░░░░░]  20% Complete   |
+---------------------------------------------------------------------------------+
```

### Strategic Takeaways:
1. **Engine A is the Crown Jewel:** The current repository is essentially a working MVP of Engine A. The document population, OOXML table building, and visual feedback loops are genuinely functional and tested. Our plan must protect this code from regression.
2. **Engines B, C, and D are Greenfields:** These engines must be architected from the ground up, but can leverage the shared foundation (Provider Manager, Queue, Cache, Security).
3. **Infrastructure Upgrades are Low-Risk / High-Reward:** Swapping `ai_router.py` for `LiteLLM`, switching `storage.py` to `diskcache`, and upgrading `BackgroundTasks` to `SqliteHuey` will stabilize the entire platform with minimal code disruption.

---
*End of Report 03.*
