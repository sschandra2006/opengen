# 15. TESTING, BENCHMARKING & VERIFICATION PLAN

> **Document ID:** `OPENGEN-TEST-015`  
> **Author:** Principal Software Architect, Senior Full-Stack Engineer, AI Infrastructure Engineer  
> **Project:** OpenGen Framework  
> **Date:** November 2026  
> **Harness:** Pytest + Playwright/PyMuPDF Visual Inspection + CI Matrix  

---

## 1. Executive Summary

This plan defines the quality assurance, automated testing, benchmarking, and visual verification strategies for OpenGen.

A primary requirement identified during the codebase audit is **resolving the test harness state contamination** where tests shared the global `.ai-document-memory/` state, causing tests to fail on repeated runs.

---

## 2. Test Isolation Architecture (`conftest.py`)

To guarantee 100% test isolation, every test run MUST operate within an isolated, ephemeral sandbox.

### Implementation Blueprint (`tests/conftest.py`):
```python
import pytest
import tempfile
import shutil
from pathlib import Path
from opengen.config import Settings
from opengen.cache.disk_store import DiskCacheManager
from opengen.queue.huey_store import init_queue

@pytest.fixture(scope="session")
def test_workspace():
    """Creates an isolated temporary directory for the entire test session."""
    temp_dir = tempfile.mkdtemp(prefix="opengen_test_ws_")
    ws_path = Path(temp_dir)
    yield ws_path
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture(autouse=True)
def isolate_test_environment(test_workspace, monkeypatch):
    """
    Automatically isolates database, cache, and upload directories per test.
    Prevents cross-test pollution and fixes the legacy test failures.
    """
    ephemeral_cache = test_workspace / "cache"
    ephemeral_uploads = test_workspace / "uploads"
    ephemeral_cache.mkdir(parents=True, exist_ok=True)
    ephemeral_uploads.mkdir(parents=True, exist_ok=True)

    monkeypatch.setenv("OPENGEN_CACHE_DIR", str(ephemeral_cache))
    monkeypatch.setenv("OPENGEN_UPLOAD_DIR", str(ephemeral_uploads))
    monkeypatch.setenv("OPENGEN_QUEUE_BACKEND", "sqlite")
    monkeypatch.setenv("OPENGEN_DB_PATH", str(ephemeral_cache / "test_meta.db"))

    # Reset cache singletons
    DiskCacheManager.reset_instance()
    yield
    DiskCacheManager.reset_instance()
```

---

## 3. Test Suite Taxonomy & Coverage Goals

```
                               TEST PYRAMID
                                   / \
                                  /   \
                                 / E2E \       15% (End-to-End Pipeline Scenarios)
                                /-------\
                               / Integr. \     35% (Engines + Provider + Visual Loop)
                              /-----------\
                             / Unit Tests  \   50% (Geometry Math, Regex, Parsers, Security)
                            /---------------\
```

### 3.1 Unit Tests (Target: > 90% Code Coverage)
- **Security Tests (`test_security.py`):**
  - Path traversal attempts (`../../etc/passwd`, symlink escapes).
  - Decompression bomb detection (files with >10:1 ratio or >100MB uncompressed).
  - Secret sanitizer scrubbing (`sk-`, `AIza`, Bearer tokens).
- **Geometry & Math Tests (`test_geometry.py`):**
  - Presentation 1, 2, 3, and 4-column card bounding boxes.
  - Non-overlapping assertions across all aspect ratios.
  - Dynamic font-scaling math under long text strings.
- **Handwriting Synthesis Math (`test_handwriting_physics.py`):**
  - Markov baseline drift verification ($\Delta y$ within $[-2.5, +2.5]$ px).
  - OpenType contextual alternate non-repetition assertion (no duplicate glyph within 3 chars).
  - College Ruled millimeter pitch math ($7.1\text{ mm} \pm 0.05\text{ mm}$).

### 3.2 Integration Tests
- **Engine A Document Tests (`test_document_engine.py`):**
  - Ported from existing `test_docx_generation.py`, `test_mapping.py`, `test_reference_extraction.py`, `test_template_analysis.py`.
  - Asserts template styles, colors, margins, and headers are preserved.
  - Verifies `cantSplit` and `tblHeader` XML injection.
  - Verifies anti-hallucination blocker prevents fake data.
- **Engine B Presentation Tests (`test_presentation_engine.py`):**
  - Generates full 10-slide PPTX from sample outline.
  - Validates output contains native shapes and Excel-backed native charts.
  - Tests single-slide regeneration without modifying surrounding slides.
- **Engine C Image Tests (`test_image_engine.py`):**
  - Tests prompt-hash caching (second call returns cached bytes instantly).
  - Verifies Pillow aspect ratio normalization and EXIF stripping.
- **Provider Manager Tests (`test_provider_manager.py`):**
  - Mocked provider tests verifying fallback chain (Gemini -> GPT-4o-mini -> Ollama).
  - Pydantic structured output validation.

### 3.3 End-to-End Tests (`test_end_to_end.py`)
- Full lifecycle tests from raw file upload through REST API / MCP tools to final artifact delivery.
- Verifies user clarification flow (`pending_clarification` -> `/api/v1/jobs/{id}/resolve` -> `completed`).

---

## 4. Performance & Cost Benchmarking Suite

OpenGen includes automated benchmarking scripts (`tests/benchmarks/`):

### 4.1 Latency Benchmarks (`bench_latency.py`)
Measures execution time per stage:
1. File hashing and validation (< 15ms).
2. Local PyMuPDF text & table extraction (< 50ms per 10 pages).
3. Local template profiling (< 80ms).
4. Deterministic OOXML assembly (< 150ms).
5. Visual validation rendering loop (< 1.5s via Word COM / LibreOffice).

### 4.2 Memory Consumption Benchmarks (`bench_memory.py`)
- Asserts that worker processes consume < 350 MB RAM during standard generation tasks.
- Verifies that scratch directories are completely purged after job completion (zero disk leakage).

### 4.3 Cost Accounting Verification (`bench_tokens.py`)
- Asserts that local deterministic operations record 0 cloud tokens.
- Asserts that prompt caching discounts (90% Anthropic/Gemini) are accurately reflected in USD cost reports.

---

## 5. Continuous Integration (CI) Matrix (GitHub Actions)

OpenGen's CI runs across all major operating systems on every Pull Request:

```yaml
name: OpenGen Test & Hardening Matrix

on: [push, pull_request]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ["3.11", "3.12", "3.13"]

    steps:
      - uses: actions/checkout@v4
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install System Dependencies (Ubuntu)
        if: runner.os == 'Linux'
        run: sudo apt-get update && sudo apt-get install -y libreoffice

      - name: Install OpenGen with Dev Dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e .[dev,weasyprint]

      - name: Run Pytest with Strict Isolation
        run: python -m pytest -v --cov=src/opengen --cov-report=xml

      - name: Security Linting (Bandit & Ruff)
        run: |
          pip install ruff bandit
          ruff check src/
          bandit -r src/ -ll
```

---
*End of Report 15.*
