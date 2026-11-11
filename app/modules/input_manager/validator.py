"""
Module 1: Document Input Management
Implements file validation, MIME type & magic byte checks, SHA-256 hashing,
duplicate detection, and immutable original storage preservation.
"""
import hashlib
import os
import re
import uuid
import zipfile
import io
from pathlib import Path
from typing import Tuple, Optional
from app.config import settings
from app.models.api_schemas import UploadResponse
from app.modules.memory_cache.storage import storage

class DocumentInputValidator:
    """Validates and securely stores uploaded documents."""

    @staticmethod
    def compute_sha256(data: bytes) -> str:
        """Computes the SHA-256 hash of a byte sequence."""
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Removes dangerous characters and path traversal attempts."""
        basename = os.path.basename(filename)
        sanitized = re.sub(r'[^a-zA-Z0-9_.-]', '_', basename)
        return sanitized or "unnamed_document"

    @classmethod
    def detect_file_type_and_verify(cls, data: bytes, filename: str) -> Tuple[str, str]:
        """
        Verifies magic bytes and extension.
        Returns: (file_type, mime_type)
        Raises: ValueError if invalid or malicious
        """
        ext = Path(filename).suffix.lower()
        if ext not in settings.ALLOWED_EXTENSIONS:
            raise ValueError(f"Unsupported file extension: '{ext}'. Allowed: {settings.ALLOWED_EXTENSIONS}")

        if len(data) == 0:
            raise ValueError("Uploaded file is empty.")

        if len(data) > settings.MAX_FILE_SIZE_BYTES:
            raise ValueError(f"File size exceeds maximum allowed limit of {settings.MAX_FILE_SIZE_BYTES / (1024*1024)}MB.")

        # Magic byte detection
        if ext == ".pdf":
            if not data.startswith(b"%PDF-"):
                raise ValueError("Invalid PDF format: Missing %PDF- header.")
            return "pdf", "application/pdf"

        elif ext == ".docx":
            # Check for ZIP header (PK\x03\x04) and presence of word/document.xml
            if not data.startswith(b"PK\x03\x04"):
                raise ValueError("Invalid DOCX format: Not a valid OpenXML ZIP package.")
            try:
                with zipfile.ZipFile(io.BytesIO(data)) as zf:
                    namelist = zf.namelist()
                    if "[Content_Types].xml" not in namelist or not any(n.startswith("word/") for n in namelist):
                        raise ValueError("Invalid DOCX package structure: Missing Word OpenXML components.")
            except zipfile.BadZipFile:
                raise ValueError("Corrupt DOCX archive.")
            return "docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

        elif ext in [".jpg", ".jpeg"]:
            if not data.startswith(b"\xff\xd8\xff"):
                raise ValueError("Invalid JPEG header bytes.")
            return "jpg", "image/jpeg"

        elif ext == ".png":
            if not data.startswith(b"\x89PNG\r\n\x1a\n"):
                raise ValueError("Invalid PNG header bytes.")
            return "png", "image/png"

        elif ext == ".txt":
            try:
                data.decode("utf-8")
            except UnicodeDecodeError:
                raise ValueError("Invalid text file: Must be UTF-8 encoded text.")
            return "txt", "text/plain"

        raise ValueError(f"Unsupported document format: {ext}")

    @classmethod
    def process_and_store(cls, data: bytes, original_filename: str) -> UploadResponse:
        """
        Validates the file, checks for duplicates, and preserves immutable source file.
        """
        safe_name = cls.sanitize_filename(original_filename)
        sha256_hash = cls.compute_sha256(data)
        file_type, mime_type = cls.detect_file_type_and_verify(data, safe_name)

        # Check duplicate
        existing = storage.get_file_by_hash(sha256_hash)
        if existing and Path(existing["storage_path"]).exists():
            return UploadResponse(
                file_id=existing["file_id"],
                filename=existing["filename"],
                file_type=existing["file_type"],
                file_size=existing["file_size"],
                sha256_hash=sha256_hash,
                is_duplicate=True
            )

        # Save new file immutably
        file_id = f"doc_{uuid.uuid4().hex[:12]}"
        dest_filename = f"{file_id}_{safe_name}"
        dest_path = settings.UPLOAD_DIR / dest_filename

        with open(dest_path, "wb") as f:
            f.write(data)

        # Register in storage
        storage.register_file(
            file_id=file_id,
            filename=safe_name,
            sha256_hash=sha256_hash,
            file_type=file_type,
            file_size=len(data),
            storage_path=str(dest_path)
        )

        return UploadResponse(
            file_id=file_id,
            filename=safe_name,
            file_type=file_type,
            file_size=len(data),
            sha256_hash=sha256_hash,
            is_duplicate=False
        )

validator = DocumentInputValidator()
