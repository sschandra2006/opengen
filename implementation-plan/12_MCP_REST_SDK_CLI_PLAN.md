# 12. MCP SERVER, REST API, PYTHON SDK & CLI SPECIFICATION

> **Document ID:** `OPENGEN-INTF-012`  
> **Author:** Principal Software Architect, Senior Full-Stack Engineer, AI Infrastructure Engineer  
> **Project:** OpenGen Framework  
> **Date:** November 2026  
> **Subsystem:** Ingress Interfaces & Client Delivery Layer  

---

## 1. Executive Summary

A defining architectural strength of OpenGen is that **all 4 interfaces share the exact same underlying generation engines and domain services**:

1. **Model Context Protocol (MCP) Server:** Allows AI coding assistants (Claude Code, Google Antigravity IDE, Cursor) to invoke OpenGen natively as agentic tools.
2. **FastAPI REST API (`/api/v1`):** Provides a versioned, asynchronous HTTP interface for web, mobile, and microservice integrations.
3. **Python SDK (`opengen.Client`):** A clean, idiomatic Python library for programmatic embedding.
4. **Typer CLI (`opengen`):** A developer-friendly command-line tool for local generation, server execution, and configuration.

---

## 2. Model Context Protocol (MCP) Server Plan

Implemented using the official `mcp[cli]>=1.2.0` standard via `FastMCP`.

- **Module Location:** `src/opengen/mcp/server.py`.
- **Supported Transports:**
  - `stdio`: Default transport for local CLI agents (Claude Desktop, Claude Code, Antigravity).
  - `sse`: Streamable HTTP server for networked agents.

### 2.1 Complete MCP Tools Catalog

| Tool Name | Parameters | Returns | Engine / Responsibility |
|---|---|---|---|
| `create_document` | `content_json: str`, `output_format: str = "docx"`, `title: str` | `file_path`, `page_count`, `cost_usd` | Engine A: Creates fresh DOCX/PDF from structured text/JSON. |
| `template_to_document` | `template_file: str`, `reference_files: list[str]`, `instruction: str` | `job_id`, `status`, `docx_path`, `pdf_path` | Engine A: Preserves Word template and populates reference facts. |
| `analyze_reference` | `file_path: str` | `extracted_fields: list`, `tables: list` | Engine A: Extracts factual knowledge and tables from reference PDF. |
| `create_presentation` | `topic: str`, `slide_count: int = 10`, `theme: str` | `pptx_path`, `slides: list`, `cost_usd` | Engine B: Generates 100% editable PPTX deck with native shapes/charts. |
| `template_to_presentation` | `template_pptx: str`, `content_json: str` | `pptx_path`, `status` | Engine B: Binds content to custom PowerPoint template layouts. |
| `generate_image` | `prompt: str`, `aspect_ratio: str`, `style: str`, `provider: str` | `image_uri`, `format`, `cost_usd` | Engine C: Generates raster (FLUX.1/DALL-E) or vector SVG (Recraft). |
| `edit_image` | `image_path: str`, `instruction: str`, `mask_path: str` | `edited_image_uri`, `cost_usd` | Engine C: Inpainting and image variation. |
| `generate_handwriting` | `text: str`, `paper_mode: str`, `ruled_type: str`, `pen_type: str` | `pdf_uri`, `transparent_mode: bool`, `print_notes` | Engine D: Anti-detection handwriting synthesis (print-ready notebook paper). |
| `get_generation_status` | `job_id: str` | `status`, `progress`, `artifacts`, `errors` | Orchestration: Polls async job progress. |
| `get_generation_cost` | `job_id: str` | `input_tokens`, `output_tokens`, `usd_cost` | Telemetry: Retrieves detailed token and financial accounting. |

### 2.2 Tool Implementation Blueprint (`src/opengen/mcp/server.py`)
```python
from mcp.server.fastmcp import FastMCP
from opengen.client import OpenGenClient

mcp = FastMCP("OpenGen", description="Self-Hostable AI Document, Presentation, Image & Handwriting Engine")
client = OpenGenClient()

@mcp.tool()
async def create_presentation(topic: str, slide_count: int = 10, theme: str = "modern_corporate") -> dict:
    """Generate a 100% native, editable Microsoft PowerPoint presentation with charts and cards."""
    deck = await client.presentations.create(topic=topic, slide_count=slide_count, theme=theme)
    return {
        "file_path": deck.file_path,
        "slide_count": len(deck.slides),
        "cost_usd": deck.cost_usd,
        "editability": "100% Native Shapes & Charts"
    }

@mcp.tool()
async def generate_handwriting(
    text: str,
    paper_mode: str = "direct_print_transparent",
    ruled_type: str = "college_ruled",
    pen_type: str = "ballpoint_blue"
) -> dict:
    """Generate realistic anti-detection handwriting for printing directly onto real physical lined paper."""
    hw = await client.handwriting.generate(
        text=text,
        paper_mode=paper_mode,
        ruled_type=ruled_type,
        pen_type=pen_type
    )
    return {
        "pdf_uri": hw.file_path,
        "page_count": hw.page_count,
        "print_instructions": hw.print_instructions
    }
```

---

## 3. Versioned REST API Specification (`/api/v1`)

- **Module Location:** `src/opengen/api/`.

### 3.1 Endpoints Overview

```
POST /api/v1/files/upload                    # Uploads & validates template/reference files
POST /api/v1/documents/generate             # Submits Document generation job
POST /api/v1/presentations/generate         # Submits Presentation generation job
POST /api/v1/images/generate                # Submits Image/Vector generation job
POST /api/v1/handwriting/generate           # Submits Handwriting generation job
GET  /api/v1/jobs/{job_id}                  # Retrieves job progress, telemetry & artifacts
POST /api/v1/jobs/{job_id}/resolve          # Resumes job with user clarification
GET  /api/v1/artifacts/{artifact_id}/dl     # Downloads generated DOCX, PPTX, PDF, or PNG
GET  /api/v1/health                         # Health check & provider status
```

### 3.2 Request Schema Example (`POST /api/v1/presentations/generate`)
```json
{
  "topic": "Future of Autonomous Agent Infrastructure",
  "slide_count": 8,
  "theme": "dark_tech",
  "include_charts": true,
  "source_document_ids": ["doc_36469746c959"]
}
```

### 3.3 Response Schema (`GET /api/v1/jobs/{job_id}`)
```json
{
  "job_id": "job_9b3f18a24c",
  "engine": "presentation",
  "status": "completed",
  "progress_percentage": 100,
  "current_step": "completed",
  "artifacts": {
    "pptx_download_url": "/api/v1/artifacts/art_8832a/dl",
    "pdf_download_url": "/api/v1/artifacts/art_8832b/dl"
  },
  "telemetry": {
    "provider_used": "google/gemini-2.5-flash",
    "input_tokens": 420,
    "output_tokens": 1850,
    "cost_usd": 0.00475,
    "local_deterministic_operations": 28
  }
}
```

---

## 4. Python SDK Client Specification (`opengen.Client`)

- **Module Location:** `src/opengen/client.py`.

```python
from opengen import OpenGenClient

client = OpenGenClient(api_key="...", default_model="gemini/gemini-2.5-flash")

# 1. Document Generation
doc = client.documents.populate(
    template="fixtures/simple_template.docx",
    references=["fixtures/digital_reference.pdf"],
    output_format="both"
)
print(f"Generated DOCX: {doc.docx_path}")
print(f"Generated PDF: {doc.pdf_path}")

# 2. Presentation Generation
deck = client.presentations.create(
    topic="Cloud Migration Strategy",
    slides=10,
    theme="modern_corporate"
)
print(f"Generated PPTX: {deck.file_path}")

# 3. Image Generation
img = client.images.generate(
    prompt="Vector minimalist icon of a neural network",
    style="vector",
    output_format="svg"
)
img.save("neural_net.svg")

# 4. Handwriting Generation
hw = client.handwriting.generate(
    text="Assignment 3: Database Normalization...",
    paper_mode="direct_print_transparent",
    ruled_type="college_ruled"
)
hw.save("print_on_lined_paper.pdf")
```

---

## 5. Typer Command-Line Interface (CLI) Specification

- **Module Location:** `src/opengen/cli/main.py`.
- **Command Syntax:**
  ```bash
  # 1. Run REST API and Web Dashboard
  opengen serve --host 127.0.0.1 --port 8000

  # 2. Run MCP Server for Claude / Antigravity IDE
  opengen mcp serve --transport stdio

  # 3. Run Async Task Queue Worker
  opengen worker --threads 4

  # 4. Generate Document via CLI
  opengen document create \
    --template ./templates/transcript.docx \
    --reference ./records.pdf \
    --output ./out/final_transcript.docx

  # 5. Generate Presentation via CLI
  opengen presentation create "AI in Supply Chain" \
    --slides 10 \
    --theme ocean_blue \
    --output ./out/deck.pptx

  # 6. Generate Realistic Handwriting
  opengen handwriting create \
    --text-file ./essay.txt \
    --paper-mode direct_print_transparent \
    --output ./out/handwriting_layer.pdf

  # 7. Check Configuration & Provider Health
  opengen config check
  ```

---
*End of Report 12.*
