# 01. OPENGEN CODEBASE AUDIT & MODULE INVENTORY

> **Document ID:** `OPENGEN-AUDIT-001`  
> **Author:** Principal Software Architect, Senior Full-Stack Engineer, AI Infrastructure Engineer  
> **Project:** OpenGen Framework Transformation  
> **Date:** November 2026  
> **Audit Target:** `f:\document generator\opengen`  
> **Repository Commit / Baseline:** Initial Document Generator Prototype  

---

## 1. Executive Summary

A comprehensive, forensic source-code audit was conducted on the existing repository at `f:\document generator\opengen`. 

The repository currently contains a functional prototype focused exclusively on **Document Generation from Templates & References** (Engine A prototype). It is implemented as a monolithic FastAPI application with an integrated lightweight SQLite caching store and an HTML/JS frontend.

### Key Audit Findings:
1. **Engine Scope:** The codebase implements an impressive proof-of-concept for **Template-to-DOCX** and **PDF-to-DOCX Reconstruction**, featuring deterministic table construction, PyMuPDF-based visual validation with auto-correction, and local regex/OCR extraction. However, **Engine B (Presentation Generation)**, **Engine C (Image Generation)**, and **Engine D (Handwriting Synthesis)** are completely absent from the source code.
2. **Interface Scope:** The only current ingress is a FastAPI REST API paired with static web assets (`app/web/static/`). There is no Model Context Protocol (MCP) server, no standalone Python SDK package, and no Command-Line Interface (CLI).
3. **Provider Integration:** AI integration is hardcoded to a dual-tier setup: local Ollama running `qwen3:8b` via direct HTTP `urllib` calls and Google Gemini Flash via `google-generativeai`. Provider abstraction is minimal; OpenAI, Anthropic, Together AI, Fireworks, and OpenRouter are not supported.
4. **State & Test Isolation Defect:** Tests write directly to the global production database (`.ai-document-memory/metadata.db`) and disk directories. As verified during testing, this caused 2 test assertions to fail due to stale cross-run data (`test_cache_invalidation_on_file_change` and `test_duplicate_detection`).
5. **Architectural Strengths:** The core OOXML table manipulation (`table_builder.py`), anti-hallucination mapping heuristics (`intelligent_mapping/`), and PyMuPDF visual inspection routines (`visual_validation/`) are high quality, deterministic, and 100% reusable in the target OpenGen architecture.

---

## 2. Repository Structure & Artifact Layout

```
f:\document generator\opengen/
├── .ai-document-memory/              # Local persistent storage & caches (Git-ignored / Run state)
│   ├── extracted_data/               # Cached reference extraction JSONs (<sha256>.json)
│   ├── generation_history/           # Output artifacts per job (<job_id>/generated.docx, .pdf)
│   ├── reference_cache/              # Internal reference files
│   ├── template_profiles/            # Cached template layout profiles (<sha256>.json)
│   ├── templates/                    # Cached template source files
│   ├── uploads/                      # Immutable uploads (<doc_id>_<name>)
│   ├── validation_reports/           # Visual inspection logs
│   └── metadata.db                   # SQLite database (files, profiles, extractions, jobs)
├── app/                              # Core application package
│   ├── config.py                     # Global settings (pydantic-settings)
│   ├── main.py                       # FastAPI application entrypoint
│   ├── models/                       # Pydantic domain & API models
│   │   ├── __init__.py
│   │   ├── api_schemas.py            # REST API input/output models
│   │   ├── extracted_info.py         # Knowledge extraction representations
│   │   ├── mapping.py                # Semantic field & table mapping models
│   │   ├── template_profile.py       # Geometry, style, font, and section models
│   │   ├── token_report.py           # Token telemetry & savings models
│   │   └── validation_report.py      # Layout inspection & issue models
│   ├── modules/                      # Pipeline stages & domain engines
│   │   ├── document_generation/      # DOCX populator, table builder, PDF reconstructor
│   │   ├── input_manager/            # File validation, MIME checks, SHA-256 hashing
│   │   ├── intelligent_mapping/      # Semantic mapping, synonym matching, anti-hallucination
│   │   ├── memory_cache/             # SQLite storage manager
│   │   ├── reference_intelligence/   # PyMuPDF, Docling, RapidOCR text/table extractors
│   │   ├── template_intelligence/    # DOCX and PDF structural profilers
│   │   ├── token_optimization/       # Ollama & Gemini router, token tracker
│   │   ├── visual_validation/        # Word COM / LibreOffice renderer, inspector, corrector
│   │   └── pipeline.py               # Master end-to-end orchestration pipeline
│   └── web/                          # Web presentation layer
│       ├── routes.py                 # FastAPI route definitions
│       └── static/                   # SPA frontend (HTML5, Vanilla JS, CSS3)
├── tests/                            # Pytest automated test suite
│   ├── fixtures/                     # Test templates, digital & scanned PDFs
│   ├── generate_fixtures.py          # Script generating synthetic fixtures
│   ├── test_docx_generation.py       # Unit tests for docx populator and reconstructor
│   ├── test_end_to_end.py            # End-to-end pipeline execution tests
│   ├── test_input_manager.py         # File validation and deduplication tests
│   ├── test_mapping.py               # Semantic matching and anti-hallucination tests
│   ├── test_reference_extraction.py  # PDF and OCR extraction tests
│   ├── test_template_analysis.py     # DOCX and PDF profiling tests
│   └── test_visual_validation.py     # Rendering and auto-correction tests
├── OPENGEN_COMPREHENSIVE_RESEARCH_REPORT.md # Completed 11-report technical research
├── README.md                         # Documentation for document generator prototype
├── requirements.txt                  # Python package dependencies
└── run_server.py                     # Uvicorn development server launcher
```

---

## 3. Comprehensive File and Module Inventory

| File Path | Primary Responsibility | LOC | Public Interface | Key Dependencies | Reusability | Technical Debt / Gaps |
|---|---|---|---|---|---|---|
| `app/config.py` | Environment config, directory initialization, limits | 65 | `Settings`, `settings` | `pydantic-settings`, `os`, `pathlib` | **High (Refactor)** | Monolithic class; creates directories as side-effect at import time; hardcodes only Gemini & Ollama. |
| `app/main.py` | FastAPI app setup, CORS, static mounts | 47 | `app`, `/`, `/api/health` | `fastapi`, `starlette` | **Medium (Refactor)** | Combines UI static asset serving with API; unversioned `/api` routes; lacks Lifespan handlers. |
| `app/models/template_profile.py` | Template geometry, fonts, margins, tables, placeholders | 96 | `TemplateProfile`, `FontProfile`, `TableProfile`, etc. | `pydantic` | **Very High** | Clean domain model; needs extension for slide presentations (Engine B) and ruled paper (Engine D). |
| `app/models/extracted_info.py` | Reference facts, tables, snippets, confidence scores | 36 | `ExtractedInformation`, `ExtractedField`, `ExtractedTable` | `pydantic` | **Very High** | Strong data representation. High reusability for multi-modal ingestion. |
| `app/models/mapping.py` | Mapping results, candidate conflicts, clarification questions | 39 | `MappingReport`, `FieldMapping`, `TableMapping` | `pydantic` | **Very High** | Core to anti-hallucination. Ready to use in unified core. |
| `app/models/validation_report.py` | Page-level issues (overflow, blank page, broken table) | 35 | `FormattingValidationReport`, `PageVisualInspection` | `pydantic` | **Very High** | Clean inspection schema. |
| `app/models/token_report.py` | Token accounting and USD savings telemetry | 37 | `TokenUsageReport` | `pydantic` | **Medium (Refactor)** | Hardcoded cost rates ($0.15/1M); needs dynamic rate table per provider. |
| `app/models/api_schemas.py` | Ingress request and status schemas | 36 | `GenerateDocumentRequest`, `DocumentJobStatus`, `UploadResponse` | `pydantic` | **Medium (Refactor)** | Document-specific. Must be modularized into `opengen.domain.job` and domain-specific schemas. |
| `app/modules/input_manager/validator.py` | Magic byte validation, SHA-256 hashing, deduplication | 136 | `DocumentInputValidator`, `validator` | `hashlib`, `zipfile`, `storage` | **High (Refactor)** | Directly queries SQLite `storage` singleton; tight coupling between validation and database IO. |
| `app/modules/template_intelligence/profiler.py` | Profile caching and analysis routing | 55 | `TemplateProfiler.get_profile()` | `storage`, `DocxAnalyzer`, `PdfAnalyzer` | **High** | Dual caching (SQLite + filesystem). Should migrate to `diskcache`. |
| `app/modules/template_intelligence/docx_analyzer.py` | Deep OOXML parsing for styles, tables, headers, placeholders | 262 | `DocxAnalyzer.analyze()` | `python-docx`, `lxml` | **Very High** | Rock-solid implementation. Retain in `opengen.engines.document`. |
| `app/modules/template_intelligence/pdf_analyzer.py` | PyMuPDF geometric bounding boxes, font sizing, tables | 246 | `PdfAnalyzer.analyze()` | `fitz (PyMuPDF)` | **Very High** | Excellent local geometric heuristics. Zero AI tokens required. |
| `app/modules/reference_intelligence/information_extractor.py` | Multi-engine reference fact extractor | 182 | `ReferenceIntelligenceEngine.process_reference()` | `PyMuPDFExtractor`, `DoclingExtractor`, `AIRouter` | **High (Refactor)** | Mixes regex parsing with local LLM entity extraction. Good fallback structure. |
| `app/modules/reference_intelligence/pymupdf_extractor.py` | Fast text, table, and heading extraction with page numbers | 99 | `PyMuPDFExtractor.extract_document()` | `fitz`, `OCRExtractor` | **Very High** | Fast, robust, deterministic local parsing. |
| `app/modules/reference_intelligence/ocr_extractor.py` | Scanned PDF page OCR fallback | 57 | `OCRExtractor.extract_page_ocr()` | `rapidocr` / `rapidocr_onnxruntime` | **High** | Works well with ONNX runtime. Needs lazy loading to avoid startup penalty. |
| `app/modules/reference_intelligence/docling_extractor.py` | Deep learning document conversion | 63 | `DoclingExtractor.extract_document()` | `docling` | **Medium (Optional)** | Heavy dependency. Should be isolated in optional extra: `opengen[docling]`. |
| `app/modules/intelligent_mapping/mapper.py` | Synonym dictionary, conflict detection, AI ambiguity resolver | 306 | `IntelligentMapper.map_document()` | `AIRouter`, `AntiHallucinationValidator` | **Very High** | Excellent logic: prevents hallucination of sensitive values, prompts user for ambiguous data. |
| `app/modules/intelligent_mapping/validator.py` | Anti-hallucination verification against reference text | 50 | `AntiHallucinationValidator.validate_mapping()` | `re` | **Very High** | Critical safety layer; verifies that mapped values actually exist in reference snippets. |
| `app/modules/document_generation/generator.py` | Dispatcher to populator or reconstructor | 47 | `DocumentGenerator.generate()` | `DocxPopulator`, `PdfReconstructor` | **High** | Clean dispatcher pattern. |
| `app/modules/document_generation/docx_populator.py` | Template preservation, run replacement, table population | 205 | `DocxPopulator.populate()` | `python-docx`, `shutil`, `TableBuilder` | **Very High** | Handles complex split runs across XML tags; enforces template formatting preservation. |
| `app/modules/document_generation/pdf_reconstructor.py` | Converts PDF layout to editable DOCX | 140 | `PdfReconstructor.reconstruct()` | `fitz`, `python-docx` | **Very High** | Accurate mapping of PDF blocks to Word paragraphs and tables. |
| `app/modules/document_generation/table_builder.py` | Advanced OOXML table borders, padding, `cantSplit`, `tblHeader` | 76 | `TableBuilder` static methods | `docx.oxml`, `parse_xml` | **Critical Component** | High-value OOXML code. Prevents broken rows and repeated headers. Essential for Engine A. |
| `app/modules/visual_validation/renderer.py` | DOCX to PDF converter | 130 | `DocumentRenderer.convert_docx_to_pdf()` | `win32com` (Windows), `libreoffice`, fallback | **High (Refactor)** | Windows COM is great locally, but requires headless LibreOffice or WeasyPrint for cross-platform Linux/Mac. |
| `app/modules/visual_validation/inspector.py` | PyMuPDF visual inspection for overflow, blank pages, broken tables | 129 | `VisualInspector.inspect()` | `fitz (PyMuPDF)` | **Very High** | Deterministic layout verification. Zero token cost. |
| `app/modules/visual_validation/auto_corrector.py` | Iterative feedback loop (tightening spacing, downscaling fonts) | 96 | `AutoCorrector.run_correction_loop()` | `DocumentRenderer`, `VisualInspector`, `docx` | **Very High** | Closed-loop visual healing mechanism up to 3 iterations. |
| `app/modules/token_optimization/ai_router.py` | Routes between local Ollama (`qwen3:8b`) and Google Gemini Flash | 119 | `AIRouter.route_task()` | `urllib`, `google.generativeai`, `json_repair` | **Medium (Refactor)** | Uses low-level `urllib` for Ollama and direct Google SDK. Must be replaced with `LiteLLM` unified provider manager. |
| `app/modules/token_optimization/tracker.py` | Tracks tokens across pipeline stages | 27 | `TokenTracker` | `TokenUsageReport` | **High** | Simple, effective tracker. |
| `app/modules/memory_cache/storage.py` | SQLite metadata and cache manager | 163 | `SQLiteStorage`, `storage` | `sqlite3` | **Medium (Refactor)** | Raw SQLite table queries without connection pooling or migrations; mix of queue state and data cache. |
| `app/modules/pipeline.py` | Master orchestrator chaining 7 pipeline steps | 175 | `DocumentGenerationPipeline.run()` | All modules | **High (Refactor)** | Synchronous runner called in FastAPI background task. Needs migration to `SqliteHuey` queue. |
| `app/web/routes.py` | REST endpoints for upload, generate, status, resolve, download | 142 | FastAPI routes | `fastapi`, `pipeline`, `storage` | **Medium (Refactor)** | Unversioned routes (`/api/...`). Needs migration to `/api/v1/...` with unified job interface. |
| `app/web/static/` | Web dashboard UI (HTML, CSS, JS) | ~1,200 | SPA browser interface | Vanilla Web Technologies | **Medium** | Functional demo UI. Can remain as embedded static dashboard. |
| `tests/generate_fixtures.py` | Creates synthetic DOCX & PDF files for tests | 176 | Helper functions | `python-docx`, `fitz`, `PIL` | **High** | Invaluable for deterministic test execution without committing large binary assets. |
| `tests/test_*.py` (7 files) | Test suite (22 test cases) | ~700 | Pytest test cases | `pytest`, `pytest-asyncio` | **High (Fix isolation)** | High test coverage of current features, but lacks isolation fixture (pollutes `.ai-document-memory/`). |

---

## 4. Architectural Analysis & Technical Debt Identification

### 4.1 Global State Pollution & Lack of Test Isolation
- **Symptom:** Running `pytest` after previous executions causes test failures:
  - `tests/test_end_to_end.py::test_cache_invalidation_on_file_change` fails because `sha256_version_2_xyz` is already present in `metadata.db`.
  - `tests/test_input_manager.py::test_duplicate_detection` fails because file entries in SQLite reference deleted files or mismatched absolute paths.
- **Root Cause:** `app/config.py` hardcodes `DB_PATH = PROJECT_ROOT / ".ai-document-memory" / "metadata.db"`. The `storage` singleton in `storage.py` initializes against this path immediately at import time. Tests do not use a temporary SQLite in-memory database or a dedicated test fixture.
- **Mitigation in OpenGen:**
  - Introduce configurable environment overrides via `pydantic-settings` (`OPENGEN_DATABASE_URL`).
  - Provide a `pytest` fixture (`conftest.py`) that initializes an isolated temporary SQLite database and scratch directory per test session.

### 4.2 Tight Coupling to Hardcoded AI Providers
- **Symptom:** `AIRouter` explicitly imports `google.generativeai` and implements custom `urllib` calls to `http://localhost:11434/api/generate`.
- **Root Cause:** Lack of a unified provider abstraction layer. Adding Anthropic Claude, OpenAI GPT-4o, Together FLUX.1, or Fireworks requires writing custom HTTP or SDK plumbing.
- **Mitigation in OpenGen:**
  - Adopt `LiteLLM` as the underlying multi-provider bridge.
  - Implement `AbstractProvider` interface supporting OpenAI, Anthropic, Gemini, Together, Fireworks, and Ollama with standardized JSON-schema output enforcement and token usage reporting.

### 4.3 Background Task Execution Model
- **Symptom:** `app/web/routes.py` uses `fastapi.BackgroundTasks` to execute `pipeline.run()`.
- **Risk:** In a multi-worker production deployment (`uvicorn -w 4`), FastAPI background tasks execute inside the ephemeral web worker process. If the worker restarts, is killed by an OOM event, or crashes during a heavy OCR operation, the job is permanently lost with no retry mechanism.
- **Mitigation in OpenGen:**
  - Implement `SqliteHuey` as the default zero-daemon background task queue. Tasks are written to an atomic SQLite queue and executed by a dedicated consumer process or thread.
  - Seamlessly support upgrading to `RedisHuey` by switching `OPENGEN_QUEUE_BACKEND=redis`.

### 4.4 Missing OpenGen Target Engines
- **Current State:** The repository is 100% focused on Document Generation.
- **Missing Engines:**
  - **Engine B (Presentation Generation):** No slide planning, no layout geometry solver, no `python-pptx` integration, no native Excel chart creation.
  - **Engine C (Image Generation):** No FLUX.1 / DALL-E / Recraft integrations, no Pillow aspect ratio or transparent alpha masking pipelines.
  - **Engine D (Pure Realistic Handwriting):** No multi-glyph alternate selection, no Brownian baseline drift, no pen physics, no physical notebook paper alignment.
- **Missing Protocols:**
  - **MCP Server:** No FastMCP implementation.
  - **Python SDK:** No `opengen` top-level client library.
  - **CLI:** No command-line interface.

---

## 5. Reusability and Preservation Verdict

> **Guiding Principle:** Working components must NOT be rewritten. They must be refactored into the modular `opengen.*` namespace.

1. **Retain and Port Directly (>90% Code Preservation):**
   - `app/modules/document_generation/table_builder.py` -> `src/opengen/engines/document/table_builder.py`
   - `app/modules/document_generation/docx_populator.py` -> `src/opengen/engines/document/docx_populator.py`
   - `app/modules/document_generation/pdf_reconstructor.py` -> `src/opengen/engines/document/pdf_reconstructor.py`
   - `app/modules/template_intelligence/docx_analyzer.py` -> `src/opengen/engines/document/template/docx_analyzer.py`
   - `app/modules/template_intelligence/pdf_analyzer.py` -> `src/opengen/engines/document/template/pdf_analyzer.py`
   - `app/modules/reference_intelligence/pymupdf_extractor.py` -> `src/opengen/engines/document/reference/pymupdf_extractor.py`
   - `app/modules/reference_intelligence/ocr_extractor.py` -> `src/opengen/engines/document/reference/ocr_extractor.py`
   - `app/modules/intelligent_mapping/mapper.py` -> `src/opengen/engines/document/mapping/mapper.py`
   - `app/modules/intelligent_mapping/validator.py` -> `src/opengen/engines/document/mapping/validator.py`
   - `app/modules/visual_validation/inspector.py` -> `src/opengen/engines/document/validation/inspector.py`
   - `app/modules/visual_validation/auto_corrector.py` -> `src/opengen/engines/document/validation/auto_corrector.py`
   - `tests/generate_fixtures.py` -> `tests/generate_fixtures.py`

2. **Refactor and Decouple:**
   - `app/config.py` -> Split into `opengen.config.Settings` with clean environment mapping.
   - `app/modules/memory_cache/storage.py` -> Separate into `opengen.queue` (Huey) and `opengen.cache` (diskcache).
   - `app/modules/visual_validation/renderer.py` -> Standardize cross-platform PDF rendering (`WeasyPrint` + headless LibreOffice + Windows COM fallback).
   - `app/modules/token_optimization/ai_router.py` -> Standardize into `opengen.providers.manager.ProviderManager` backed by `LiteLLM`.

3. **Construct New Systems:**
   - `src/opengen/engines/presentation/` (Engine B)
   - `src/opengen/engines/image/` (Engine C)
   - `src/opengen/engines/handwriting/` (Engine D)
   - `src/opengen/mcp/` (FastMCP Server)
   - `src/opengen/cli/` (Typer CLI)
   - `src/opengen/client/` (Python SDK Client)

---
*End of Report 01.*
