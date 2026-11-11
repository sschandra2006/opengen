"""
Tests for Module 3: Reference Document Intelligence.
"""
from pathlib import Path
from app.modules.reference_intelligence.information_extractor import ReferenceIntelligenceEngine
from app.modules.reference_intelligence.pymupdf_extractor import PyMuPDFExtractor

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

def test_digital_pdf_extraction():
    ref_path = FIXTURES_DIR / "digital_reference.pdf"
    engine = ReferenceIntelligenceEngine()
    info = engine.process_reference(str(ref_path), file_hash="hash_digital_ref")

    assert info.filename == "digital_reference.pdf"
    assert len(info.fields) > 0

    field_dict = {f.field: f.value for f in info.fields}
    assert any("alexander" in str(v).lower() for v in field_dict.values())
    assert any("3.88" in str(v) for v in field_dict.values())
    assert any("stu-98421" in str(v).lower() for v in field_dict.values())

    # Check source and confidence tracking
    for field in info.fields:
        assert field.source == "digital_reference.pdf"
        assert field.page >= 1
        assert field.confidence > 0.7

def test_scanned_pdf_ocr_extraction():
    scanned_path = FIXTURES_DIR / "scanned_reference.pdf"
    parsed = PyMuPDFExtractor.extract_document(str(scanned_path))
    # Scanned PDF text should be extracted via OCR or text layer
    assert len(parsed["full_text"]) > 0
    assert "Alexander Wright" in parsed["full_text"] or "ENROLLMENT" in parsed["full_text"]
