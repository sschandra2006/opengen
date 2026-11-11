"""
Tests for OpenGen Python SDK Client.
Verifies programmatic developer API across all 4 generation engines.
"""
import pytest
from pathlib import Path
from opengen import OpenGenClient


@pytest.fixture
def client():
    return OpenGenClient()


def test_sdk_presentation_generation(client, tmp_path):
    dest = tmp_path / "sdk_deck.pptx"
    res = client.presentations.create(
        topic="Machine Learning Ingestion Pipelines",
        slide_count=5,
        theme="ocean_blue",
        output_pptx_path=dest
    )
    assert res.file_path == str(dest)
    assert Path(res.file_path).exists()
    assert res.slide_count == 5
    assert len(res.slides) == 5


def test_sdk_handwriting_generation(client, tmp_path):
    dest = tmp_path / "sdk_handwriting.pdf"
    res = client.handwriting.generate(
        text="Sample lecture notes for SDK unit test.",
        paper_mode="direct_print_transparent",
        output_pdf_path=dest
    )
    assert res.file_path == str(dest)
    assert Path(res.file_path).exists()
    assert res.page_count == 1
    assert res.transparent_mode is True


def test_sdk_image_generation(client, tmp_path):
    res = client.images.generate(
        prompt="Modern minimalist gradient cube",
        style="vector"
    )
    assert Path(res.file_path).exists()
    assert res.is_vector is True

    # Test .save() helper method
    saved_dest = tmp_path / "custom_cube.svg"
    saved = res.save(saved_dest)
    assert Path(saved).exists()


def test_sdk_jobs_and_telemetry(client):
    job = client.jobs.get("job_sdk_999")
    assert job is not None
    assert job.id == "job_sdk_999"

    cost = client.jobs.get_cost()
    assert isinstance(cost, dict)
    assert "total_cost_usd" in cost
