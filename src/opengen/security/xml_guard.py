"""
Decompression bomb protection and defused XML parsing for Office packages.
"""
import io
import zipfile
import defusedxml.minidom
from opengen.config import settings
from opengen.domain.errors import SecurityViolationError

class SafePackageExtractor:
    """Safely inspects and extracts XML components from ZIP archives (DOCX, PPTX)."""

    @classmethod
    def verify_zip_limits(cls, data_bytes: bytes):
        """Checks for zip bomb characteristics: compression ratios and total size."""
        if len(data_bytes) == 0:
            raise SecurityViolationError("File is empty.")

        if len(data_bytes) > settings.MAX_FILE_SIZE_BYTES:
            raise SecurityViolationError(f"Compressed file exceeds {settings.MAX_FILE_SIZE_BYTES / (1024*1024)}MB limit.")

        total_uncompressed = 0
        try:
            with zipfile.ZipFile(io.BytesIO(data_bytes)) as zf:
                for info in zf.infolist():
                    total_uncompressed += info.file_size
                    if info.compress_size > 0:
                        ratio = info.file_size / float(info.compress_size)
                        if ratio > settings.MAX_EXPANSION_RATIO:
                            raise SecurityViolationError(f"Decompression bomb ratio ({ratio:.1f}:1) exceeds limit.")

                    if total_uncompressed > settings.MAX_UNCOMPRESSED_BYTES:
                        raise SecurityViolationError("Uncompressed archive contents exceed 100MB limit.")
        except zipfile.BadZipFile:
            raise SecurityViolationError("Corrupted or malformed ZIP package.")

    @classmethod
    def parse_xml_safely(cls, xml_bytes: bytes) -> str:
        """Parses XML using defusedxml to neutralize Billion Laughs & entity expansion attacks."""
        dom = defusedxml.minidom.parseString(xml_bytes)
        return dom.toxml()
