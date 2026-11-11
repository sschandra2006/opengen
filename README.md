# AI Document Generation Engine
### Intelligent PDF Analysis + Word Template Preservation + Automated DOCX Generation

A production-grade AI-powered document generation system that accepts formatting templates (DOCX or PDF) alongside one or more reference documents, extracts factual information, maps fields without hallucination, and generates professional, editable Microsoft Word (.docx) and rendered PDF documents.

---

## Key Capabilities

1. **DOCX Template Preservation:** Directly populates existing Word documents while preserving typography, fonts, colors, margins, tables, headers, footers, and alignments.
2. **PDF Template Reconstruction:** Dissects PDF layout, typography, tables, and images to generate an editable Word document matching the original visual structure.
3. **Reference Intelligence (Docling & RapidOCR):** Extracts tables, entities, key-values, and dates from digital and scanned PDFs, tracking source filename, page number, and extraction confidence.
4. **Anti-Hallucination Semantic Mapping:** Maps template fields to extracted reference evidence. Strictly prevents hallucination of sensitive fields (names, dates, financial figures, grades). Prompts user clarification for ambiguous or conflicting facts.
5. **Visual Layout Quality Validation & Auto-Correction:** Renders Word documents into PDF (via native Office / LibreOffice) and uses PyMuPDF to inspect pages for text overflow, boundary clipping, blank pages, and broken tables, auto-correcting spacing and typography up to 3 iterations.
6. **Token Optimization Engine:** Offloads OCR, layout profiling, table extraction, hashing, and rendering to local 0-token deterministic code. Routes classification and preliminary extraction to local **Ollama (Qwen3:8B)** and reserves **Google Gemini Flash** for complex semantic reasoning.
7. **Document Memory & Caching:** Persistent SHA-256 caching in `.ai-document-memory/` avoids re-analyzing unchanged templates and references.
8. **Interactive Web Interface:** Modern web UI with live progress indicators across all 8 pipeline stages, interactive clarification dialog, visual quality telemetry, and instant DOCX / PDF downloads.

---

## Architecture Overview

```
INPUT DOCUMENTS (DOCX, PDF, Images, Text)
       |
       v
MODULE 1: FILE VALIDATION & HASHING (SHA-256, MIME & Magic Bytes Check)
       |
       +-----------------------+
       |                       |
       v                       v
MODULE 2: TEMPLATE INTELLIGENCE  MODULE 3: REFERENCE INTELLIGENCE
(DOCX & PDF Layout Profiling)     (Docling + RapidOCR + Page Tracking)
       |                       |
       +-----------+-----------+
                   |
                   v
MODULE 4: INTELLIGENT MAPPING & ANTI-HALLUCINATION AUDIT
                   |
                   v
MODULE 5 & 6: DOCX GENERATION & ADVANCED TABLE BUILDER
                   |
                   v
MODULE 7: VISUAL VALIDATION (PDF Render + PyMuPDF Page Inspector)
                   |  (Auto-Correction Loop <= 3 Iterations)
                   v
FINAL OUTPUT: EDITABLE DOCX + PDF + MAPPING & TOKEN TELEMETRY
```

---

## Directory Structure

```
document_generator/
├── app/
│   ├── config.py                     # Environment, limits, AI keys, paths
│   ├── main.py                       # FastAPI application entrypoint
│   ├── models/                       # Validated Pydantic models
│   │   ├── template_profile.py       # Margins, FontProfile, TableProfile, TemplateProfile
│   │   ├── extracted_info.py         # ExtractedField, ExtractedTable, ExtractedInformation
│   │   ├── mapping.py                # FieldMapping, TableMapping, MappingReport
│   │   ├── validation_report.py      # FormattingValidationReport, PageVisualInspection
│   │   ├── token_report.py           # TokenUsageReport
│   │   └── api_schemas.py            # UploadResponse, JobStatus, Request models
│   ├── modules/
│   │   ├── input_manager/            # Module 1: File validation & immutable preservation
│   │   ├── template_intelligence/    # Module 2: DOCX and PDF template analyzers
│   │   ├── reference_intelligence/   # Module 3: Docling & PyMuPDF & RapidOCR extractors
│   │   ├── intelligent_mapping/      # Module 4: Semantic mapper & anti-hallucination engine
│   │   ├── document_generation/      # Modules 5 & 6: DOCX populator & PDF reconstructor
│   │   ├── visual_validation/        # Module 7: Renderer, inspector & auto-corrector
│   │   ├── token_optimization/       # Module 8: Qwen3:8B local Ollama & Gemini Flash router
│   │   ├── memory_cache/             # Module 9: SQLite metadata & persistent cache
│   │   └── pipeline.py               # Master end-to-end pipeline orchestrator
│   └── web/
│       ├── routes.py                 # REST API endpoints
│       └── static/                   # Modern responsive Web UI (HTML, CSS, JS)
├── tests/                            # Automated test suite (20+ tests)
│   ├── fixtures/                     # Test templates, digital & scanned PDFs
│   ├── test_input_manager.py
│   ├── test_template_analysis.py
│   ├── test_reference_extraction.py
│   ├── test_mapping.py
│   ├── test_docx_generation.py
│   ├── test_visual_validation.py
│   └── test_end_to_end.py
├── .ai-document-memory/              # Persistent memory, SQLite DB, cache files
├── requirements.txt
├── run_server.py
└── README.md
```

---

## Getting Started

### 1. Requirements
- Python 3.11+ (Tested on Python 3.13)
- Ollama with `qwen3:8b` (Local inference)
- Google Gemini API key (Optional for cloud reasoning; defaults to local Qwen3:8B)
- Microsoft Word (Windows COM) or LibreOffice (Headless) for visual PDF rendering

### 2. Setup Environment
```bash
python -m pip install -r requirements.txt
```

### 3. Run Automated Tests
```bash
python -m pytest -v
```

### 4. Start the Application Server
```bash
python run_server.py
```
Open your browser and navigate to:
```
http://localhost:8000
```

---

## Token Optimization Strategy

| Task Category | Engine | Cloud Token Cost |
| :--- | :--- | :--- |
| File Hashing, Size, Security | Local Python / SHA-256 | **0 Tokens** |
| DOCX Style & Layout Analysis | Local python-docx + lxml | **0 Tokens** |
| PDF Layout, Margins, Geometry | Local PyMuPDF / fitz | **0 Tokens** |
| Table Boundary & Header Detection | Local PyMuPDF / Docling | **0 Tokens** |
| Scanned PDF OCR | Local RapidOCR (ONNX) | **0 Tokens** |
| Deterministic Entity & Date Match | Local Regex Pattern Matcher | **0 Tokens** |
| Document Rendering & Inspection | Local Word COM / PyMuPDF | **0 Tokens** |
| Preliminary Semantic Classification | Local Ollama (`qwen3:8b`) | **0 Cloud Tokens** |
| Complex Ambiguity & Mapping | Google Gemini Flash API | ~500 - 1500 Tokens |

# opengen
