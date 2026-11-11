"""
Template Profiler coordinator.
Handles caching, routing to DOCX or PDF analyzers, and saving profiles.
"""
import json
import logging
from pathlib import Path
from app.config import settings
from app.models.template_profile import TemplateProfile
from app.modules.memory_cache.storage import storage
from app.modules.template_intelligence.docx_analyzer import DocxAnalyzer
from app.modules.template_intelligence.pdf_analyzer import PdfAnalyzer

logger = logging.getLogger(__name__)

class TemplateProfiler:
    """Extracts and caches high-fidelity template profiles."""

    @classmethod
    def get_profile(cls, file_path: str, file_hash: str) -> TemplateProfile:
        # 1. Check SQLite & disk cache first (Token & latency optimization)
        cached_data = storage.get_template_profile(file_hash)
        if cached_data:
            logger.info("Template profile retrieved from cache (0 AI tokens used)")
            return TemplateProfile(**cached_data)

        disk_cache_file = settings.PROFILES_DIR / f"{file_hash}.json"
        if disk_cache_file.exists():
            try:
                with open(disk_cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    storage.save_template_profile(file_hash, data.get("document_type", "general"), data)
                    return TemplateProfile(**data)
            except Exception as e:
                logger.warning(f"Failed reading disk cache: {e}")

        # 2. Perform deep analysis based on file extension
        ext = Path(file_path).suffix.lower()
        if ext == ".docx":
            profile = DocxAnalyzer.analyze(file_path, file_hash)
        elif ext == ".pdf":
            profile = PdfAnalyzer.analyze(file_path, file_hash)
        else:
            raise ValueError(f"Unsupported template format: '{ext}'. Must be .docx or .pdf")

        # 3. Save to cache
        profile_dict = profile.model_dump()
        storage.save_template_profile(file_hash, profile.document_type, profile_dict)
        try:
            with open(disk_cache_file, "w", encoding="utf-8") as f:
                json.dump(profile_dict, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not persist profile to disk: {e}")

        return profile
