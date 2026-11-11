"""
Tests for Cross-Generation State Isolation and output/ Directory Architecture.
Verifies that Run N never pollutes Run N+1 (credentials, cost telemetry, caches, filenames, or files).
"""
import os
from pathlib import Path
import docx
import pymupdf

from opengen import OpenGenClient
from opengen.config import settings
from opengen.engines.handwriting.engine import handwriting_engine
from opengen.engines.image.cache import ImageCache
from opengen.mcp.server import tool_create_document


FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def test_output_dir_uses_isolated_per_run_folders():
    client = OpenGenClient()
    r1 = client.presentations.create(topic="Topic A", slide_count=3)
    r2 = client.presentations.create(topic="Topic A", slide_count=3)

    assert r1.job_id != r2.job_id
    p1 = Path(r1.pptx_path)
    p2 = Path(r2.pptx_path)

    assert p1.exists() and p2.exists()
    # Must sit inside separate output/presentations/<run>/ folders
    assert p1.parent != p2.parent
    assert p1.parent.parent == settings.OUTPUT_DIR / "presentations"
    assert (p1.parent / "metadata.json").exists()
    assert (p2.parent / "metadata.json").exists()


def test_client_credentials_do_not_leak_to_env_or_other_clients():
    orig_openai = os.environ.get("OPENAI_API_KEY")
    orig_gemini = os.environ.get("GEMINI_API_KEY")
    orig_model = settings.DEFAULT_LLM_MODEL

    c1 = OpenGenClient(api_key="isolated_key_alpha", default_model="openai/gpt-4o")
    c2 = OpenGenClient(api_key="isolated_key_beta", default_model="gemini/gemini-2.5-flash")

    # Global process state must NEVER be overwritten
    assert os.environ.get("OPENAI_API_KEY") == orig_openai
    assert os.environ.get("GEMINI_API_KEY") == orig_gemini
    assert settings.DEFAULT_LLM_MODEL == orig_model

    # Each client retains its isolated configuration
    assert c1.api_key == "isolated_key_alpha"
    assert c1.default_model == "openai/gpt-4o"
    assert c2.api_key == "isolated_key_beta"
    assert c2.default_model == "gemini/gemini-2.5-flash"


def test_image_cache_parameter_separation_and_output_resilience():
    # Hash must distinguish transparency and output format
    h_opaque = ImageCache.compute_hash("Clean cube", "1:1", "minimal", "flux", "png", False)
    h_trans = ImageCache.compute_hash("Clean cube", "1:1", "minimal", "flux", "png", True)
    h_svg = ImageCache.compute_hash("Clean cube", "1:1", "minimal", "flux", "svg", False)
    assert len({h_opaque, h_trans, h_svg}) == 3

    client = OpenGenClient()
    img1 = client.images.generate(prompt="Test Vector Cube", style="vector", output_format="svg")
    path1 = Path(img1.file_path)
    assert path1.exists()

    # Delete output file of run 1 — cache store must survive independently and regenerate run 2 cleanly
    path1.unlink()
    assert not path1.exists()

    img2 = client.images.generate(prompt="Test Vector Cube", style="vector", output_format="svg")
    path2 = Path(img2.file_path)
    assert path2.exists()
    assert path2.parent != path1.parent


def test_handwriting_singleton_isolation_and_multipage(tmp_path):
    long_text = " ".join(["Algorithm complexity depends on recurrence bounds and memory locality."] * 25)
    out1 = tmp_path / "hw1.pdf"
    out2 = tmp_path / "hw2.pdf"

    handwriting_engine.generate_handwriting(long_text, str(out1), transparent_mode=True, seed=101)
    handwriting_engine.generate_handwriting(long_text, str(out2), transparent_mode=True, seed=101)

    with pymupdf.open(str(out1)) as d1, pymupdf.open(str(out2)) as d2:
        # Multi-page output preserved without truncation at page 1
        assert len(d1) >= 2
        assert len(d2) == len(d1)


def test_document_partial_regenerate_cell_preserves_source(tmp_path):
    client = OpenGenClient()
    src_docx = tmp_path / "source_table.docx"
    doc = docx.Document()
    tbl = doc.add_table(rows=2, cols=2)
    tbl.cell(0, 0).text = "Header A"
    tbl.cell(0, 1).text = "Header B"
    tbl.cell(1, 0).text = "Original Value"
    tbl.cell(1, 1).text = "100"
    doc.save(str(src_docx))

    regen_out = client.documents.regenerate_element(
        docx_path=src_docx,
        table_index=0,
        row_index=1,
        col_index=0,
        new_text="Updated Value"
    )

    assert Path(regen_out).exists()
    assert Path(regen_out) != src_docx

    # Verify original file was NOT mutated
    orig_doc = docx.Document(str(src_docx))
    assert orig_doc.tables[0].cell(1, 0).text == "Original Value"

    # Verify generated output contains updated cell
    new_doc = docx.Document(regen_out)
    assert new_doc.tables[0].cell(1, 0).text == "Updated Value"


def test_mcp_tool_create_document_without_template():
    res = tool_create_document(
        content_json='{"title": "Isolation Architecture", "sections": [{"heading": "Overview", "body": "Verified cleanly."}]}',
        title="Isolation Architecture"
    )
    assert res["status"] == "success"
    assert res["job_id"] is not None
    assert Path(res["docx_path"]).exists()


def test_persisted_job_ledger_lookup():
    client = OpenGenClient()
    hw = client.handwriting.generate(text="Per-job tracking verification.")
    rec = client.jobs.get(hw.job_id)

    assert rec is not None
    assert rec.job_id == hw.job_id
    assert rec.engine == "handwriting"
    assert rec.artifacts["pdf"] == hw.file_path
