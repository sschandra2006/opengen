"""
Tests for Module 2: Template Intelligence Engine.
"""
from pathlib import Path
from app.modules.template_intelligence.docx_analyzer import DocxAnalyzer
from app.modules.template_intelligence.pdf_analyzer import PdfAnalyzer
from app.modules.template_intelligence.profiler import TemplateProfiler

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

def test_simple_docx_template_analysis():
    docx_path = FIXTURES_DIR / "simple_template.docx"
    profile = DocxAnalyzer.analyze(str(docx_path), file_hash="hash_simple")

    assert profile.file_type == "docx"
    assert profile.page_size in ["A4", "Letter", "Custom"]
    assert profile.margins.top == 0.8
    assert len(profile.placeholders) >= 5

    placeholder_keys = {p.raw_key for p in profile.placeholders}
    assert "{{student_name}}" in placeholder_keys
    assert "{{student_id}}" in placeholder_keys
    assert "{{gpa}}" in placeholder_keys

def test_complex_docx_table_analysis():
    docx_path = FIXTURES_DIR / "complex_template.docx"
    profile = DocxAnalyzer.analyze(str(docx_path), file_hash="hash_complex")

    assert len(profile.tables) >= 1
    table = profile.tables[0]
    assert table.num_rows == 4
    assert table.num_cols == 3

    # Verify placeholders inside table cells are identified
    placeholder_keys = {p.raw_key for p in profile.placeholders}
    assert "{{cs101_grade}}" in placeholder_keys

def test_pdf_template_analysis():
    pdf_path = FIXTURES_DIR / "sample_template.pdf"
    profile = PdfAnalyzer.analyze(str(pdf_path), file_hash="hash_pdf")

    assert profile.file_type == "pdf"
    assert profile.total_pages_approx == 1
    # Check bracket placeholders detected
    field_names = {p.field_name for p in profile.placeholders}
    assert any("student_name" in f for f in field_names)

def test_template_profiler_caching():
    docx_path = FIXTURES_DIR / "simple_template.docx"
    profile1 = TemplateProfiler.get_profile(str(docx_path), "cache_test_hash")
    # Second call must come from storage
    profile2 = TemplateProfiler.get_profile(str(docx_path), "cache_test_hash")
    assert profile1.file_hash == profile2.file_hash
    assert len(profile1.placeholders) == len(profile2.placeholders)
