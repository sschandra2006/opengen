"""
OpenGen Configuration Module.
Provides centralized settings management for directories, providers, queues, and security.
"""
import os
from pathlib import Path
from typing import Optional, Set
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="OPENGEN_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow"
    )

    # Base Filesystem Paths
    BASE_DIR: Path = PROJECT_ROOT
    DATA_DIR: Path = PROJECT_ROOT / "data"
    CACHE_DIR: Path = PROJECT_ROOT / "cache"
    UPLOAD_DIR: Path = PROJECT_ROOT / "data" / "uploads"
    OUTPUT_DIR: Path = PROJECT_ROOT / "data" / "outputs"
    DB_PATH: Path = PROJECT_ROOT / "cache" / "metadata.db"

    # Queue Settings
    QUEUE_BACKEND: str = "sqlite"  # "sqlite" or "redis"
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security & File Limits
    MAX_FILE_SIZE_BYTES: int = 50 * 1024 * 1024  # 50MB
    MAX_UNCOMPRESSED_BYTES: int = 100 * 1024 * 1024  # 100MB
    MAX_EXPANSION_RATIO: float = 10.0
    ALLOWED_EXTENSIONS: Set[str] = {".docx", ".pdf", ".jpg", ".jpeg", ".png", ".txt", ".pptx", ".svg"}

    # AI Provider Defaults
    DEFAULT_LLM_MODEL: str = "gemini/gemini-2.5-flash"
    DEFAULT_FAST_MODEL: str = "openai/gpt-4o-mini"
    DEFAULT_LOCAL_MODEL: str = "ollama/qwen3:8b"
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # API Keys (read from environment)
    GEMINI_API_KEY: Optional[str] = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    OPENAI_API_KEY: Optional[str] = os.environ.get("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = os.environ.get("ANTHROPIC_API_KEY")
    TOGETHER_API_KEY: Optional[str] = os.environ.get("TOGETHER_API_KEY") or os.environ.get("TOGETHERAI_API_KEY")
    RECRAFT_API_KEY: Optional[str] = os.environ.get("RECRAFT_API_KEY")

    # Processing Limits
    MAX_VALIDATION_ATTEMPTS: int = 3
    DEFAULT_CONFIDENCE_THRESHOLD: float = 0.70

    def ensure_directories(self):
        """Idempotently creates necessary working directories."""
        for path in [self.DATA_DIR, self.CACHE_DIR, self.UPLOAD_DIR, self.OUTPUT_DIR]:
            path.mkdir(parents=True, exist_ok=True)

settings = Settings()
