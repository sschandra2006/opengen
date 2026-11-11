"""
Template Profiler coordinator.
Handles caching via DiskCacheManager and routing to DOCX or PDF analyzers.
"""
import logging
from pathlib import Path
from opengen.domain.document import TemplateProfile
from opengen.cache.disk_store import cache_manager
from opengen.engines.document.template.docx_analyzer import DocxAnalyzer
from opengen.engines.document.template.pdf_analyzer import PdfAnalyzer

logger = logging.getLogger(__name__)

class TemplateProfiler:
    """Extracts and caches high-fidelity template profiles."""

    @classmethod
    def get_profile(cls, file_path: str, file_hash: str) -> TemplateProfile:
        # 1. Check L2 Diskcache (0 AI tokens used)
        cached_data = cache_manager.get_template_profile(file_hash)
        if cached_data:
            logger.info("Template profile retrieved from persistent L2 cache (0 tokens)")
            return TemplateProfile.model_validate(cached_data)

        # 2. Perform deep analysis based on file extension
        ext = Path(file_path).suffix.lower()
        if ext == ".docx":
            profile = DocxAnalyzer.analyze(file_path, file_hash)
        elif ext == ".pdf":
            profile = PdfAnalyzer.analyze(file_path, file_hash)
        else:
            raise ValueError(f"Unsupported template format: '{ext}'. Must be .docx or .pdf")

        # 3. Store in L2 persistent cache
        cache_manager.set_template_profile(file_hash, profile.model_dump())
        return profile
