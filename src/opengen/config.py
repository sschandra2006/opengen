"""
OpenGen Configuration Module.
Provides centralized settings management for directories, providers, queues, and security.
"""
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Set, Tuple
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def resolve_default_model() -> str:
    """
    Intelligently auto-resolves the default LLM model based on available environment credentials,
    ensuring OpenGen never assumes a single vendor and works out-of-the-box with any configured provider.
    Priority:
      1. OPENGEN_MODEL or OPENGEN_DEFAULT_PRIMARY_MODEL (explicit override)
      2. ANTHROPIC_API_KEY -> anthropic/claude-3-5-haiku-20241022
      3. OPENAI_API_KEY -> openai/gpt-4o-mini
      4. DEEPSEEK_API_KEY -> deepseek/deepseek-chat
      5. GEMINI_API_KEY / GOOGLE_API_KEY -> gemini/gemini-2.5-flash
      6. OPENROUTER_API_KEY -> openrouter/auto
      7. Default local / offline fallback -> ollama/qwen3:8b
    """
    if os.environ.get("OPENGEN_MODEL"):
        return os.environ["OPENGEN_MODEL"]
    if os.environ.get("OPENGEN_DEFAULT_PRIMARY_MODEL"):
        return os.environ["OPENGEN_DEFAULT_PRIMARY_MODEL"]
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "anthropic/claude-3-5-haiku-20241022"
    if os.environ.get("OPENAI_API_KEY"):
        return "openai/gpt-4o-mini"
    if os.environ.get("DEEPSEEK_API_KEY"):
        return "deepseek/deepseek-chat"
    if os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"):
        return "gemini/gemini-2.5-flash"
    if os.environ.get("OPENROUTER_API_KEY"):
        return "openrouter/auto"
    return "ollama/qwen3:8b"


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
    BRANDS_DIR: Path = PROJECT_ROOT / "data" / "brands"
    OUTPUT_DIR: Path = PROJECT_ROOT / "output"
    TEMPLATES_DIR: Path = PROJECT_ROOT / "templates"
    SFX_DIR: Path = PROJECT_ROOT / "data" / "sfx"
    DB_PATH: Path = PROJECT_ROOT / "cache" / "metadata.db"
    JOBS_DB_PATH: Path = PROJECT_ROOT / "cache" / "jobs.db"

    # Queue Settings
    QUEUE_BACKEND: str = "sqlite"  # "sqlite" or "redis"
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security & File Limits
    MAX_FILE_SIZE_BYTES: int = 50 * 1024 * 1024  # 50MB
    MAX_UNCOMPRESSED_BYTES: int = 100 * 1024 * 1024  # 100MB
    MAX_EXPANSION_RATIO: float = 10.0
    ALLOWED_EXTENSIONS: Set[str] = {".docx", ".pdf", ".jpg", ".jpeg", ".png", ".txt", ".pptx", ".svg"}

    # AI Provider Defaults (Dynamically resolved across all frontier, open-weight & local models)
    DEFAULT_LLM_MODEL: str = resolve_default_model()
    DEFAULT_PRIMARY_MODEL: str = resolve_default_model()
    DEFAULT_FAST_MODEL: str = "openai/gpt-4o-mini"
    DEFAULT_LOCAL_MODEL: str = "ollama/qwen3:8b"
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # API Keys (read from environment)
    GEMINI_API_KEY: Optional[str] = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    OPENAI_API_KEY: Optional[str] = os.environ.get("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = os.environ.get("ANTHROPIC_API_KEY")
    DEEPSEEK_API_KEY: Optional[str] = os.environ.get("DEEPSEEK_API_KEY")
    OPENROUTER_API_KEY: Optional[str] = os.environ.get("OPENROUTER_API_KEY")
    TOGETHER_API_KEY: Optional[str] = os.environ.get("TOGETHER_API_KEY") or os.environ.get("TOGETHERAI_API_KEY")
    RECRAFT_API_KEY: Optional[str] = os.environ.get("RECRAFT_API_KEY")
    VLLM_BASE_URL: str = os.environ.get("VLLM_BASE_URL", "http://localhost:8000/v1")
    LOCAL_LLM_BASE_URL: str = os.environ.get("LOCAL_LLM_BASE_URL", "http://localhost:1234/v1")

    # Processing Limits
    MAX_VALIDATION_ATTEMPTS: int = 3
    DEFAULT_CONFIDENCE_THRESHOLD: float = 0.70

    # Adaptive Hardware Governor Settings
    ENABLE_HARDWARE_ADAPTATION: bool = True
    HARDWARE_TIER: Optional[str] = os.environ.get("OPENGEN_HARDWARE_TIER")
    MAX_RAM_THRESHOLD_PCT: float = 88.0

    def ensure_directories(self):
        """Idempotently creates necessary working directories."""
        for path in [self.DATA_DIR, self.CACHE_DIR, self.UPLOAD_DIR, self.OUTPUT_DIR, self.SFX_DIR]:
            path.mkdir(parents=True, exist_ok=True)

    def allocate_run_dir(self, engine: str, job_id: Optional[str] = None) -> Tuple[str, Path]:
        """
        Allocates an isolated per-generation directory under output/<engine>/<timestamp>_<job_id>/
        so consecutive or concurrent runs never overwrite or collide with each other.
        """
        jid = job_id or f"job_{uuid.uuid4().hex[:10]}"
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")[:20]
        run_dir = self.OUTPUT_DIR / engine / f"{ts}_{jid}"
        run_dir.mkdir(parents=True, exist_ok=True)
        return jid, run_dir


settings = Settings()
