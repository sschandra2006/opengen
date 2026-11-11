"""
Configuration module for the AI Document Generation Engine.
Manages file paths, external tool integrations, AI model configurations, and security constraints.
"""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="allow")
    # Base paths
    BASE_DIR: Path = PROJECT_ROOT
    MEMORY_DIR: Path = PROJECT_ROOT / ".ai-document-memory"
    UPLOAD_DIR: Path = PROJECT_ROOT / ".ai-document-memory" / "uploads"
    TEMPLATE_CACHE_DIR: Path = PROJECT_ROOT / ".ai-document-memory" / "templates"
    REFERENCE_CACHE_DIR: Path = PROJECT_ROOT / ".ai-document-memory" / "reference_cache"
    EXTRACTED_DATA_DIR: Path = PROJECT_ROOT / ".ai-document-memory" / "extracted_data"
    PROFILES_DIR: Path = PROJECT_ROOT / ".ai-document-memory" / "template_profiles"
    HISTORY_DIR: Path = PROJECT_ROOT / ".ai-document-memory" / "generation_history"
    VALIDATION_DIR: Path = PROJECT_ROOT / ".ai-document-memory" / "validation_reports"
    DB_PATH: Path = PROJECT_ROOT / ".ai-document-memory" / "metadata.db"
    
    # File limits & security
    MAX_FILE_SIZE_BYTES: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: set = {".docx", ".pdf", ".jpg", ".jpeg", ".png", ".txt"}
    ALLOWED_MIME_TYPES: set = {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/pdf",
        "image/jpeg",
        "image/png",
        "text/plain"
    }

    # AI Configurations
    GEMINI_API_KEY: Optional[str] = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    GEMINI_MODEL: str = "gemini-2.5-flash"
    OLLAMA_BASE_URL: str = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.environ.get("OLLAMA_MODEL", "qwen3:8b")
    USE_LOCAL_FALLBACK: bool = True

    # Processing limits
    MAX_VALIDATION_ATTEMPTS: int = 3
    DEFAULT_CONFIDENCE_THRESHOLD: float = 0.70

    # LibreOffice / PDF rendering
    LIBREOFFICE_PATH: Optional[str] = None
    TESSERACT_PATH: Optional[str] = None

settings = Settings()

# Ensure critical directories exist
for path in [
    settings.MEMORY_DIR,
    settings.UPLOAD_DIR,
    settings.TEMPLATE_CACHE_DIR,
    settings.REFERENCE_CACHE_DIR,
    settings.EXTRACTED_DATA_DIR,
    settings.PROFILES_DIR,
    settings.HISTORY_DIR,
    settings.VALIDATION_DIR,
]:
    path.mkdir(parents=True, exist_ok=True)
