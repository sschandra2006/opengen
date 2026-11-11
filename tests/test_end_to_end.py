"""
End-to-End System Tests for Complete Pipeline.
"""
from pathlib import Path
from app.modules.input_manager.validator import validator
from app.modules.pipeline import DocumentGenerationPipeline

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

def test_full_pipeline_docx_template():
    # 1. Register Template File
    with open(FIXTURES_DIR / "simple_template.docx", "rb") as f:
        templ_res = validator.process_and_store(f.read(), "simple_template.docx")

    # 2. Register Reference Document
    with open(FIXTURES_DIR / "digital_reference.pdf", "rb") as f:
        ref_res = validator.process_and_store(f.read(), "digital_reference.pdf")

    # 3. Execute Pipeline
    pipeline = DocumentGenerationPipeline()
    job_status = pipeline.run(
        job_id="test_e2e_job_001",
        template_file_id=templ_res.file_id,
        reference_file_ids=[ref_res.file_id],
        instruction="Generate complete transcript for Alexander Wright",
        output_format="both"
    )

    assert job_status.status in ["completed", "pending_clarification"]
    if job_status.status == "completed":
        assert job_status.progress_percentage == 100
        assert job_status.docx_download_url is not None
        assert job_status.pdf_download_url is not None
        assert job_status.validation_report is not None
        assert job_status.token_usage is not None
        assert job_status.token_usage["local_operations_count"] > 0

def test_full_pipeline_pdf_template():
    # 1. Register PDF Template File
    with open(FIXTURES_DIR / "sample_template.pdf", "rb") as f:
        templ_res = validator.process_and_store(f.read(), "sample_template.pdf")

    # 2. Register Reference Document
    with open(FIXTURES_DIR / "digital_reference.pdf", "rb") as f:
        ref_res = validator.process_and_store(f.read(), "digital_reference.pdf")

    # 3. Execute Pipeline
    pipeline = DocumentGenerationPipeline()
    job_status = pipeline.run(
        job_id="test_e2e_pdf_002",
        template_file_id=templ_res.file_id,
        reference_file_ids=[ref_res.file_id],
        output_format="both"
    )

    assert job_status.status in ["completed", "pending_clarification"]
    if job_status.status == "completed":
        assert job_status.progress_percentage == 100
        assert job_status.docx_download_url is not None

def test_cache_invalidation_on_file_change():
    from app.modules.template_intelligence.profiler import TemplateProfiler
    from app.modules.memory_cache.storage import storage

    # Register initial version
    hash_v1 = "sha256_version_1_abc"
    templ_path = str(FIXTURES_DIR / "simple_template.docx")
    p1 = TemplateProfiler.get_profile(templ_path, hash_v1)

    # When file content changes, hash is different
    hash_v2 = "sha256_version_2_xyz"
    # Storage should not have hash_v2 yet
    assert storage.get_template_profile(hash_v2) is None
    p2 = TemplateProfiler.get_profile(templ_path, hash_v2)
    assert p2.file_hash == hash_v2
