"""
Tests for Module 5 & 6: Word Document Generation and Advanced Tables.
"""
from pathlib import Path
import docx
from app.modules.template_intelligence.docx_analyzer import DocxAnalyzer
from app.modules.reference_intelligence.information_extractor import ReferenceIntelligenceEngine
from app.modules.intelligent_mapping.mapper import IntelligentMapper
from app.modules.document_generation.generator import DocumentGenerator

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

def test_docx_template_population_and_preservation(tmp_path):
    templ_path = FIXTURES_DIR / "simple_template.docx"
    ref_path = FIXTURES_DIR / "digital_reference.pdf"

    profile = DocxAnalyzer.analyze(str(templ_path), "simple_hash")
    engine = ReferenceIntelligenceEngine()
    ref_info = engine.process_reference(str(ref_path), "ref_hash")

    mapper = IntelligentMapper()
    mapping_report = mapper.map_document(profile, [ref_info])

    out_docx = tmp_path / "populated_result.docx"
    DocumentGenerator.generate(
        template_path=str(templ_path),
        output_docx_path=str(out_docx),
        mapping_report=mapping_report,
        template_profile=profile
    )

    assert out_docx.exists()
    doc = docx.Document(str(out_docx))

    # Verify formatting preservation
    sec = doc.sections[0]
    assert sec.top_margin.inches == 0.8
    assert "ACADEMIC TRANSCRIPT OFFICIAL REPORT" in sec.header.paragraphs[0].text

    # Verify placeholder values were injected
    full_text = "\n".join(p.text for p in doc.paragraphs)
    assert "Alexander Wright" in full_text
    assert "STU-98421" in full_text
    assert "3.88" in full_text
    assert "{{student_name}}" not in full_text
    assert "{{student_id}}" not in full_text

def test_pdf_template_reconstruction(tmp_path):
    pdf_templ_path = FIXTURES_DIR / "sample_template.pdf"
    ref_path = FIXTURES_DIR / "digital_reference.pdf"

    from app.modules.template_intelligence.pdf_analyzer import PdfAnalyzer
    profile = PdfAnalyzer.analyze(str(pdf_templ_path), "pdf_hash")
    engine = ReferenceIntelligenceEngine()
    ref_info = engine.process_reference(str(ref_path), "ref_hash")

    mapper = IntelligentMapper()
    mapping_report = mapper.map_document(profile, [ref_info])

    out_docx = tmp_path / "reconstructed_from_pdf.docx"
    DocumentGenerator.generate(
        template_path=str(pdf_templ_path),
        output_docx_path=str(out_docx),
        mapping_report=mapping_report,
        template_profile=profile
    )

    assert out_docx.exists()
    doc = docx.Document(str(out_docx))
    full_text = "\n".join(p.text for p in doc.paragraphs)
    assert "Alexander Wright" in full_text or "STU-98421" in full_text or "3.88" in full_text
