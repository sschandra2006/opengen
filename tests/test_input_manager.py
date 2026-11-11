"""
Tests for Module 1: Document Input Management.
"""
import pytest
from pathlib import Path
from app.modules.input_manager.validator import DocumentInputValidator, validator

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

def test_valid_docx_upload():
    file_path = FIXTURES_DIR / "simple_template.docx"
    with open(file_path, "rb") as f:
        data = f.read()

    resp = validator.process_and_store(data, "simple_template.docx")
    assert resp.file_id.startswith("doc_")
    assert resp.file_type == "docx"
    assert resp.file_size == len(data)
    assert len(resp.sha256_hash) == 64

def test_duplicate_detection():
    file_path = FIXTURES_DIR / "simple_template.docx"
    with open(file_path, "rb") as f:
        data = f.read()

    resp1 = validator.process_and_store(data, "simple_template.docx")
    resp2 = validator.process_and_store(data, "simple_template_copy.docx")
    assert resp2.is_duplicate is True
    assert resp2.file_id == resp1.file_id

def test_malformed_pdf():
    malformed_data = b"This is not a real PDF file header"
    with pytest.raises(ValueError, match="Invalid PDF format"):
        validator.detect_file_type_and_verify(malformed_data, "broken.pdf")

def test_empty_file():
    with pytest.raises(ValueError, match="Uploaded file is empty"):
        validator.detect_file_type_and_verify(b"", "empty.docx")

def test_unsupported_extension():
    with pytest.raises(ValueError, match="Unsupported file extension"):
        validator.detect_file_type_and_verify(b"some content", "script.exe")

def test_filename_sanitization():
    sanitized = DocumentInputValidator.sanitize_filename("../../etc/passwd.docx")
    assert "/" not in sanitized
    assert ".." not in sanitized
