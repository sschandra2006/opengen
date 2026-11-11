"""
Tests for Module 7: Visual Document Validation & Auto-Correction.
"""
from pathlib import Path
import docx
from app.modules.visual_validation.renderer import DocumentRenderer
from app.modules.visual_validation.inspector import VisualInspector
from app.modules.visual_validation.auto_corrector import AutoCorrector

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

def test_renderer_and_inspector(tmp_path):
    docx_path = FIXTURES_DIR / "simple_template.docx"
    pdf_out = tmp_path / "rendered.pdf"

    produced_pdf = DocumentRenderer.convert_docx_to_pdf(str(docx_path), str(pdf_out))
    assert Path(produced_pdf).exists()

    report = VisualInspector.inspect(str(produced_pdf), template_page_count=1)
    assert report.is_valid is True
    assert report.generated_page_count >= 1

def test_auto_corrector_loop(tmp_path):
    docx_path = FIXTURES_DIR / "complex_template.docx"
    pdf_out = tmp_path / "rendered_complex.pdf"

    report, final_pdf = AutoCorrector.run_correction_loop(
        docx_path=str(docx_path),
        pdf_path=str(pdf_out),
        template_page_count=1,
        max_iterations=2
    )

    assert Path(final_pdf).exists()
    assert report.status in ["passed", "auto_corrected", "warning"]
