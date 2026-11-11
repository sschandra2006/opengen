"""
Tests for Module 4: Intelligent Information Mapping.
"""
from pathlib import Path
from app.modules.template_intelligence.docx_analyzer import DocxAnalyzer
from app.modules.reference_intelligence.information_extractor import ReferenceIntelligenceEngine
from app.modules.intelligent_mapping.mapper import IntelligentMapper
from app.modules.intelligent_mapping.validator import AntiHallucinationValidator
from app.models.mapping import FieldMapping

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

def test_direct_and_semantic_mapping():
    docx_path = FIXTURES_DIR / "simple_template.docx"
    ref_path = FIXTURES_DIR / "digital_reference.pdf"

    profile = DocxAnalyzer.analyze(str(docx_path), "simple_hash")
    engine = ReferenceIntelligenceEngine()
    ref_info = engine.process_reference(str(ref_path), "ref_hash")

    mapper = IntelligentMapper()
    report = mapper.map_document(
        template_profile=profile,
        reference_docs=[ref_info]
    )

    assert "student_name" in report.mappings
    assert "Alexander Wright" in str(report.mappings["student_name"].mapped_value)
    assert report.mappings["student_name"].status == "verified"

    assert "gpa" in report.mappings
    assert "3.88" in str(report.mappings["gpa"].mapped_value)

def test_anti_hallucination_prevents_fake_data():
    # If a sensitive field has no source and was not user-provided
    fake_mapping = FieldMapping(
        template_field="student_name",
        mapped_value="Invented Name",
        source="",
        confidence=0.5,
        status="tentative"
    )
    is_valid = AntiHallucinationValidator.validate_mapping(fake_mapping)
    assert is_valid is False
    assert fake_mapping.status == "missing"

def test_conflicting_information_detection():
    docx_path = FIXTURES_DIR / "simple_template.docx"
    ref_path1 = FIXTURES_DIR / "digital_reference.pdf"
    ref_path2 = FIXTURES_DIR / "conflicting_reference.pdf"

    profile = DocxAnalyzer.analyze(str(docx_path), "simple_hash")
    engine = ReferenceIntelligenceEngine()
    info1 = engine.process_reference(str(ref_path1), "ref_hash1")
    info2 = engine.process_reference(str(ref_path2), "ref_hash2")

    mapper = IntelligentMapper()
    report = mapper.map_document(
        template_profile=profile,
        reference_docs=[info1, info2]
    )

    # Check that conflicting fields (e.g. GPA or Name) are flagged
    assert len(report.conflicting_fields) > 0 or any(m.status == "conflict" for m in report.mappings.values())
