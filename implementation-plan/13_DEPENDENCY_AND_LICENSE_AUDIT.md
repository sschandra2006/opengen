# 13. DEPENDENCY & LICENSE COMPATIBILITY AUDIT

> **Document ID:** `OPENGEN-DEPS-013`  
> **Author:** Principal Software Architect, Senior Full-Stack Engineer, AI Infrastructure Engineer  
> **Project:** OpenGen Framework  
> **Date:** November 2026  
> **Licensing Target:** Apache 2.0 Permissive Framework  

---

## 1. Executive Summary & Licensing Strategy

OpenGen is designed as an open-source, commercially viable, permissive framework distributed under the **Apache 2.0 License**.

To ensure that corporations, independent developers, and academic institutions can embed, self-host, and extend OpenGen without legal friction:
1. **Zero Viral Copyleft in Core:** Libraries under AGPLv3 (e.g., PyMuPDF) or GPLv3 (e.g., Marker) must never be statically linked into the core engine without clean permissive fallbacks or commercial license compliance.
2. **Strict LGPLv2.1 Isolation:** `docxtpl` (LGPLv2.1) is used strictly as a dynamically linked, unmodified external library behind an abstracted `TemplateEngine` port.
3. **Modular Dependency Architecture:** Heavy libraries (such as IBM Docling with PyTorch, or Diffusers for local image generation) are isolated as optional extras (`pip install opengen[docling]`), ensuring the core install remains lightweight (< 80 MB) and installs in seconds.

---

## 2. Granular Dependency Classification Matrix

### Category A: Already Installed & Reusable

| Package Name | Installed Version | License | OpenGen Role | Footprint | Evaluation |
|---|---|---|---|---|---|
| `fastapi` | `>=0.115.0` | MIT | REST API Layer | ~15 MB | Excellent modern async web framework. Keep in core. |
| `uvicorn` | `>=0.30.0` | BSD-3-Clause | ASGI Web Server | ~5 MB | High-performance ASGI runtime. Keep in core. |
| `pydantic` | `>=2.8.0` | MIT | Domain & DTO Validation | ~10 MB | Fast C-core (pydantic-core). Core data model backbone. |
| `pydantic-settings` | `>=2.4.0` | MIT | Environment Configuration | ~2 MB | Clean `.env` and environment mapping. |
| `python-docx` | `>=1.1.2` | MIT | OOXML Document Assembly | ~8 MB | The foundation of Engine A (tables, runs, paragraphs). |
| `pillow` | `>=10.4.0` | HPND (Permissive) | Image Processing | ~12 MB | Foundation for Engine C and Engine D raster operations. |
| `httpx` | `>=0.27.0` | BSD-3-Clause | Async HTTP Client | ~4 MB | Used for asynchronous provider calls. |
| `json-repair` | `>=0.30.0` | MIT | Malformed JSON Healing | < 1 MB | Essential safety net for fixing slightly broken LLM JSON. |
| `pytest` | `>=8.3.0` | MIT | Test Harness | ~10 MB | Test runner. Move to `[dev]` extra. |

---

### Category B: Installed but Requiring Improvement or Isolation

| Package Name | Installed Version | License | OpenGen Role | Current Issue | Architectural Resolution |
|---|---|---|---|---|---|
| `docxtpl` | `>=0.19.0` | LGPLv2.1 | Jinja2 Word Templating | Installed but never imported in code. | Wrap inside isolated `DocxTplEngine` port. Maintain pure MIT `DocxPopulator` fallback. |
| `pymupdf` (`fitz`) | `>=1.24.0` | AGPLv3 / Commercial | PDF Parsing & Visual Inspection | Direct import across 4 files; AGPL viral risk for commercial closed-source users. | Abstract behind `IDocumentParser` interface. Provide pure-permissive fallback (`pypdf` + `pdfplumber`). |
| `docling` | `>=2.15.0` | MIT / Apache-2.0 | Deep Document Conversion | Pulls ~2 GB PyTorch/Torchvision; heavy on pure CPU. | Move out of base install into optional extra: `pip install opengen[docling]`. |
| `rapidocr` / `onnxruntime` | `>=3.1.0` / `>=1.19.0` | Apache 2.0 | Scanned PDF OCR | Eagerly loaded during startup. | Implement lazy loading: load ONNX models only on first scanned page encounter. |
| `google-generativeai` | `>=0.8.0` | Apache 2.0 | Gemini API Calls | Tightly coupled in `ai_router.py`. | Replace with unified `LiteLLM` bridge (`litellm[google]`). |

---

### Category C: New Mandatory Dependencies

| Package Name | Target Version | License | Role in OpenGen | Footprint | Concrete Rationale |
|---|---|---|---|---|---|
| `python-pptx` | `>=1.0.2` | MIT | Engine B (Presentation) | ~8 MB | Indispensable library for creating native, editable PowerPoint (`.pptx`) decks. |
| `litellm` | `>=1.55.0` | MIT | Unified Provider Bridge | ~25 MB | Replaces custom `urllib` and vendor SDKs with universal OpenAI-compatible translator. |
| `mcp[cli]` | `>=1.2.0` | MIT | Model Context Protocol | ~12 MB | Official Anthropic FastMCP standard for Claude and Antigravity IDE tools. |
| `huey` | `>=2.5.0` | MIT | Zero-Daemon Async Queue | ~2 MB | Lightweight SQLite task queue. Zero broker processes required for local self-hosting. |
| `diskcache` | `>=5.6.3` | Apache 2.0 | Persistent L2 Cache | ~3 MB | SQLite-backed caching with automatic LRU and TTL eviction. Replaces raw custom SQLite tables. |
| `typer` | `>=0.12.5` | MIT | Command-Line Interface | ~4 MB | Modern, elegant CLI framework built on Click and Pydantic types. |
| `structlog` | `>=24.4.0` | Apache 2.0 / MIT | Structured Observability | ~2 MB | Structured JSON logging with context correlation (`job_id`) and key sanitization. |
| `defusedxml` | `>=0.7.1` | Python-2.0 | Security Hardening | < 1 MB | Neutralizes XML Entity Expansion and Billion Laughs attacks across DOCX/PPTX unzipping. |

---

### Category D: Optional Dependencies (Modular Extras)

```toml
[project.optional-dependencies]
# IBM Deep Document Layout & Table Analysis
docling = [
    "docling>=2.15.0",
    "torch>=2.4.0",
    "torchvision>=0.19.0"
]

# High-Quality W3C CSS Paged Media PDF Generation
weasyprint = [
    "weasyprint>=62.0"
]

# Production Distributed Queue
redis = [
    "redis>=5.0.0"
]

# Local GPU Image Synthesis (Diffusers)
diffusers = [
    "diffusers>=0.30.0",
    "transformers>=4.44.0",
    "accelerate>=0.33.0"
]

# Development & Testing
dev = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
    "ruff>=0.6.0",
    "mypy>=1.11.0"
]

# Complete Kitchen-Sink Installation
all = [
    "opengen[weasyprint,docling,redis]"
]
```

---

### Category E: Rejected Dependencies & Concrete Technical Rationale

| Candidate Library | Proposed Role | Rejected In Favor Of | Concrete Technical Rationale |
|---|---|---|---|
| **LangChain / LlamaIndex** | Orchestration & RAG | Custom Clean Architecture + `LiteLLM` | Massive dependency bloat (>150 transitive packages), volatile breaking API changes, high latency overhead. |
| **Celery** | Asynchronous Task Queue | `Huey` (`SqliteHuey`) | Celery requires mandatory external brokers (Redis/RabbitMQ), complex daemon setup, and heavy Windows multiprocessing friction. Huey runs out of the box with SQLite. |
| **Puppeteer / Playwright** | Headless Chrome PDF Export | `WeasyPrint` | Headless Chrome consumes 10x more RAM (~800 MB per worker), suffers from zombie processes, and lacks native CSS Paged Media `@page` margin counters. |
| **Marker (GPLv3)** | PDF to Markdown Parser | `PyMuPDF` + `Docling` | **Viral GPLv3 License:** Cannot be integrated into an Apache 2.0 framework without forcing the entire project into GPLv3. |
| **Tabula-py** | PDF Table Extraction | Native PyMuPDF `find_tables()` | Tabula requires a system Java Runtime Environment (JRE). Pure Python/C libraries eliminate runtime friction. |
| **pywhatkit** | Handwriting Generation | Custom `HandwritingEngine` (Engine D) | Extremely naive: simply renders TTF font on a canvas. Produces identical repeated glyphs, perfectly flat baselines, and gets detected instantly. |

---

## 3. Full `pyproject.toml` Build Specification

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "opengen"
version = "1.0.0"
description = "Modular, open-source, self-hostable AI generation framework for documents, presentations, images, and handwriting."
readme = "README.md"
license = { text = "Apache-2.0" }
authors = [{ name = "OpenGen Maintainers" }]
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn>=0.30.0",
    "pydantic>=2.8.0",
    "pydantic-settings>=2.4.0",
    "python-docx>=1.1.2",
    "python-pptx>=1.0.2",
    "docxtpl>=0.19.0",
    "litellm>=1.55.0",
    "mcp[cli]>=1.2.0",
    "huey>=2.5.0",
    "diskcache>=5.6.3",
    "typer>=0.12.5",
    "pillow>=10.4.0",
    "pymupdf>=1.24.0",
    "rapidocr>=3.1.0",
    "onnxruntime>=1.19.0",
    "defusedxml>=0.7.1",
    "structlog>=24.4.0",
    "json-repair>=0.30.0",
    "httpx>=0.27.0"
]

[project.scripts]
opengen = "opengen.cli.main:app"

[tool.hatch.build.targets.wheel]
packages = ["src/opengen"]
```

---
*End of Report 13.*
