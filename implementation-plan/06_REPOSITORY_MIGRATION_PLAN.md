# 06. REPOSITORY MIGRATION & RESTRUCTURING PLAN

> **Document ID:** `OPENGEN-MIGRATE-006`  
> **Author:** Principal Software Architect, Senior Full-Stack Engineer, AI Infrastructure Engineer  
> **Project:** OpenGen Framework  
> **Date:** November 2026  
> **Target Package:** `opengen` (under `src/` layout)  

---

## 1. Executive Summary

This plan specifies the structural transition of the current repository from a flat `app/` folder into a production-grade, standard Python package adhering to the modern `src` layout (`src/opengen/`).

### Strict Constraint Reminder:
- **No file reorganization or code deletion will take place during this analysis phase.**
- This document serves as the approved migration blueprint that will be executed in Phase 1 of the implementation roadmap.

---

## 2. Directory Structure Mapping: Current vs Target

```
CURRENT DIRECTORY STRUCTURE                  TARGET DIRECTORY STRUCTURE
---------------------------------------      ---------------------------------------
f:\document generator\opengen/               f:\document generator\opengen/
├── app/                                     ├── pyproject.toml                  [NEW - Hatch build system]
│   ├── config.py                            ├── uv.lock                         [NEW - Pinned lockfile]
│   ├── main.py                              ├── README.md                       [UPDATED - OpenGen Framework]
│   ├── models/                              ├── LICENSE                         [NEW - Apache 2.0]
│   │   ├── api_schemas.py                   ├── src/
│   │   ├── extracted_info.py                │   └── opengen/                    [NEW - Root Python Package]
│   │   ├── mapping.py                       │       ├── __init__.py             [NEW - Public API exports]
│   │   ├── template_profile.py              │       ├── config.py               [MOVED/REFACTORED from app/config.py]
│   │   ├── client.py                [NEW - Python SDK Client]
│   │   ├── token_report.py                  │       ├── domain/                 [NEW - Clean Domain Entities]
│   │   └── validation_report.py             │       │   ├── job.py
│   ├── modules/                             │       │   ├── document.py
│   │   ├── document_generation/             │       │   ├── presentation.py
│   │   ├── input_manager/                   │       │   ├── image.py
│   │   ├── intelligent_mapping/             │       │   ├── handwriting.py
│   │   ├── memory_cache/                    │       │   └── errors.py
│   │   ├── reference_intelligence/          │       ├── engines/                [NEW - Modular Generation Engines]
│   │   ├── template_intelligence/           │       │   ├── document/           [PORTED from app/modules/doc*]
│   │   ├── token_optimization/              │       │   ├── presentation/       [NEW - Engine B]
│   │   ├── visual_validation/               │       │   ├── image/              [NEW - Engine C]
│   │   └── pipeline.py                      │       │   └── handwriting/        [NEW - Engine D]
│   └── web/                                 │       ├── providers/              [NEW - LiteLLM Multi-Provider]
│       ├── routes.py                        │       ├── queue/                  [NEW - SqliteHuey Task Queue]
│       └── static/                          │       ├── cache/                  [NEW - diskcache Persistent Cache]
├── tests/                                   │       ├── security/               [NEW - PathGuard & DefusedXML]
├── .ai-document-memory/                     │       ├── api/                    [PORTED/VERSIONED from app/web/]
├── OPENGEN_COMPREHENSIVE_RESEARCH_REPORT.md │       ├── mcp/                    [NEW - FastMCP Tools]
├── requirements.txt                         │       └── cli/                    [NEW - Typer CLI]
└── run_server.py                            ├── tests/                          [UPDATED with conftest.py & isolation]
                                             └── implementation-plan/            [19 Implementation Reports]
```

---

## 3. Granular File-by-File Migration Matrix

| Existing Path | Action | Target Path | Reason for Change | Dependencies |
|---|---|---|---|---|
| `requirements.txt` | **Convert** | `pyproject.toml` | Modern standard packaging with optional extras (`[docling]`, `[diffusers]`, `[redis]`). | `hatchling` |
| `run_server.py` | **Retain/Wrap** | `run_server.py` | Convenience script for local testing; points to `opengen.api.app:app`. | `uvicorn` |
| `app/config.py` | **Refactor & Move** | `src/opengen/config.py` | Eliminate side-effect directory creation on import; add provider and queue configs. | `pydantic-settings` |
| `app/main.py` | **Refactor & Move** | `src/opengen/api/app.py` | Version REST API under `/api/v1/`, isolate static mounting, add Lifespan handler. | `fastapi` |
| `app/models/template_profile.py` | **Move** | `src/opengen/domain/document.py` | Consolidate template and document geometry models into clean domain entity. | `pydantic` |
| `app/models/extracted_info.py` | **Move** | `src/opengen/domain/document.py` | Reference data extraction models become part of core domain. | `pydantic` |
| `app/models/mapping.py` | **Move** | `src/opengen/domain/document.py` | Field and table mapping entities. | `pydantic` |
| `app/models/validation_report.py` | **Move** | `src/opengen/domain/document.py` | Visual inspection models. | `pydantic` |
| `app/models/token_report.py` | **Move** | `src/opengen/domain/provider.py` | Generalize token and cost telemetry across all AI providers. | `pydantic` |
| `app/models/api_schemas.py` | **Split** | `src/opengen/api/schemas.py` & `src/opengen/domain/job.py` | Decouple pure domain job representations from HTTP payload DTOs. | `pydantic` |
| `app/modules/input_manager/validator.py` | **Refactor & Move** | `src/opengen/security/validator.py` | Decouple from SQLite `storage` singleton; enforce `is_relative_to()`. | `hashlib`, `defusedxml` |
| `app/modules/document_generation/table_builder.py` | **Move Directly** | `src/opengen/engines/document/table_builder.py` | Preserve 100% of tested OOXML table construction logic. | `docx.oxml` |
| `app/modules/document_generation/docx_populator.py` | **Move Directly** | `src/opengen/engines/document/docx_populator.py` | Preserve template style preservation and placeholder substitution logic. | `python-docx` |
| `app/modules/document_generation/pdf_reconstructor.py` | **Move Directly** | `src/opengen/engines/document/pdf_reconstructor.py` | Preserve PDF layout reconstruction into editable Word documents. | `fitz`, `python-docx` |
| `app/modules/document_generation/generator.py` | **Refactor & Move** | `src/opengen/engines/document/engine.py` | Expand into unified `DocumentEngine` supporting DOCX, Jinja2, and PDF export. | `opengen.domain` |
| `app/modules/template_intelligence/docx_analyzer.py` | **Move Directly** | `src/opengen/engines/document/template/docx_analyzer.py` | Deep OOXML template layout and placeholder parsing. | `python-docx`, `lxml` |
| `app/modules/template_intelligence/pdf_analyzer.py` | **Move Directly** | `src/opengen/engines/document/template/pdf_analyzer.py` | Deep PDF geometric profiling. | `fitz` |
| `app/modules/template_intelligence/profiler.py` | **Refactor & Move** | `src/opengen/engines/document/template/profiler.py` | Point caching to `opengen.cache.diskcache` instead of ad-hoc SQLite. | `opengen.cache` |
| `app/modules/reference_intelligence/pymupdf_extractor.py` | **Move Directly** | `src/opengen/engines/document/reference/pymupdf_extractor.py` | Fast local PDF fact, table, and heading extraction. | `fitz` |
| `app/modules/reference_intelligence/ocr_extractor.py` | **Move Directly** | `src/opengen/engines/document/reference/ocr_extractor.py` | Scanned PDF OCR fallback with RapidOCR. | `rapidocr` |
| `app/modules/reference_intelligence/docling_extractor.py` | **Move Directly** | `src/opengen/engines/document/reference/docling_extractor.py` | Deep learning document parsing (isolated in optional extra). | `docling` |
| `app/modules/reference_intelligence/information_extractor.py` | **Refactor & Move** | `src/opengen/engines/document/reference/extractor.py` | Decouple from old `ai_router.py`; call `opengen.providers.manager`. | `opengen.providers` |
| `app/modules/intelligent_mapping/mapper.py` | **Refactor & Move** | `src/opengen/engines/document/mapping/mapper.py` | Connect to `ProviderManager` for semantic ambiguity resolution. | `opengen.providers` |
| `app/modules/intelligent_mapping/validator.py` | **Move Directly** | `src/opengen/engines/document/mapping/validator.py` | Anti-hallucination verification logic. | `re` |
| `app/modules/visual_validation/inspector.py` | **Move Directly** | `src/opengen/engines/document/validation/inspector.py` | PyMuPDF visual overflow and blank page detection. | `fitz` |
| `app/modules/visual_validation/auto_corrector.py` | **Move Directly** | `src/opengen/engines/document/validation/auto_corrector.py` | Closed-loop 3-iteration visual layout healing. | `python-docx` |
| `app/modules/visual_validation/renderer.py` | **Refactor & Move** | `src/opengen/engines/document/validation/renderer.py` | Add WeasyPrint direct HTML-to-PDF engine alongside Word COM/LibreOffice. | `weasyprint`, `fitz` |
| `app/modules/token_optimization/ai_router.py` | **Replace** | `src/opengen/providers/manager.py` | Deprecate low-level `urllib` & Google SDK; replace with unified `LiteLLM` bridge. | `litellm` |
| `app/modules/token_optimization/tracker.py` | **Refactor & Move** | `src/opengen/telemetry/cost_tracker.py` | Universal token and dynamic USD cost calculation. | `opengen.domain` |
| `app/modules/memory_cache/storage.py` | **Split & Replace** | `src/opengen/cache/disk_store.py` & `src/opengen/queue/huey_store.py` | Separate caching from task queue persistence. | `diskcache`, `huey` |
| `app/modules/pipeline.py` | **Refactor & Move** | `src/opengen/engines/document/pipeline.py` | Keep as Engine A execution sequence callable by Huey tasks. | `opengen.engines` |
| `app/web/routes.py` | **Refactor & Move** | `src/opengen/api/v1/routes.py` | Version under `/api/v1/`, expose all 4 engines and job polling. | `fastapi` |
| `app/web/static/` | **Retain/Move** | `src/opengen/api/static/` | Preserve SPA frontend dashboard for local browser users. | Vanilla Web Assets |
| `tests/generate_fixtures.py` | **Retain** | `tests/generate_fixtures.py` | Preserved test fixture generation script. | `python-docx`, `fitz` |
| `tests/test_*.py` | **Update & Port** | `tests/test_*.py` | Update import statements from `app.*` to `opengen.*`. | `pytest` |
| None | **Create** | `tests/conftest.py` | Test isolation fixtures: in-memory DB, temp upload dir, mocked providers. | `pytest` |

---

## 4. Step-by-Step Migration Execution Sequence

When Phase 1 begins, the migration will be executed in 6 atomic stages to prevent broken intermediate states:

### Stage 1: Build System & Foundation
1. Create `pyproject.toml` at repository root defining project metadata, entrypoints, and dependencies.
2. Initialize directory skeleton: `src/opengen/{domain,engines,providers,queue,cache,security,api,mcp,cli}`.
3. Add `src/opengen/__init__.py` and version declaration (`__version__ = "1.0.0"`).

### Stage 2: Domain & Infrastructure Porting
1. Move domain models into `src/opengen/domain/`.
2. Implement `src/opengen/security/` (`PathGuard`, `DefusedXML`, `LogSanitizer`).
3. Implement `src/opengen/cache/` using `diskcache.FanoutCache`.
4. Implement `src/opengen/queue/` using `SqliteHuey`.
5. Implement `src/opengen/providers/` wrapping `LiteLLM`.

### Stage 3: Engine A (Document) Porting
1. Port `docx_populator.py`, `table_builder.py`, and `pdf_reconstructor.py` into `src/opengen/engines/document/`.
2. Port template intelligence and reference intelligence extractors into `src/opengen/engines/document/{template,reference}/`.
3. Port mapping and anti-hallucination validator into `src/opengen/engines/document/mapping/`.
4. Port visual validation inspector, renderer, and auto-corrector into `src/opengen/engines/document/validation/`.

### Stage 4: Test Suite Porting & Isolation Fix
1. Create `tests/conftest.py` providing isolated `tmp_path` fixtures for cache and queue databases.
2. Update all imports in `tests/test_*.py` from `from app.modules...` to `from opengen.engines.document...`.
3. Run `python -m pytest` and verify that all 22 tests pass with 100% green status (resolving the 2 previous isolation failures).

### Stage 5: Ingress Layer Deployment
1. Build `src/opengen/api/v1/routes.py` and `app.py`.
2. Build `src/opengen/mcp/server.py` using `FastMCP`.
3. Build `src/opengen/cli/main.py` using `Typer`.
4. Build `src/opengen/client.py` Python SDK client.

### Stage 6: Deprecation & Legacy Cleanup
1. Verify that `python run_server.py`, `pytest`, and `opengen --help` work seamlessly.
2. Safely archive legacy `app/` folder into `.archive/legacy_app/` or remove once target is 100% verified.

---
*End of Report 06.*
