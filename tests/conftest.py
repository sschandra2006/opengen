"""
Pytest configuration and test isolation fixtures.
Prevents cross-test pollution by redirecting caches and storage to isolated temporary directories.
"""
import pytest
import tempfile
import shutil
import sys
from pathlib import Path

# Add project root and src/ to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from opengen.cache.disk_store import DiskCacheManager

@pytest.fixture(scope="session")
def test_temp_workspace():
    """Creates an isolated temporary folder for the entire test session."""
    tmp = tempfile.mkdtemp(prefix="opengen_test_env_")
    yield Path(tmp)
    shutil.rmtree(tmp, ignore_errors=True)

@pytest.fixture(autouse=True)
def isolate_opengen_test_state(test_temp_workspace, monkeypatch):
    """
    Automatically redirects cache, upload, and database directories
    to fresh temporary paths per test to prevent test cross-contamination.
    """
    isolated_cache = test_temp_workspace / "cache"
    isolated_uploads = test_temp_workspace / "uploads"
    isolated_cache.mkdir(parents=True, exist_ok=True)
    isolated_uploads.mkdir(parents=True, exist_ok=True)

    monkeypatch.setenv("OPENGEN_CACHE_DIR", str(isolated_cache))
    monkeypatch.setenv("OPENGEN_UPLOAD_DIR", str(isolated_uploads))
    monkeypatch.setenv("OPENGEN_DB_PATH", str(isolated_cache / "test_metadata.db"))

    # Reset cache manager singleton
    DiskCacheManager.reset_instance()

    # Isolate legacy app storage if imported
    try:
        from app.modules.memory_cache.storage import storage
        from app.config import settings as legacy_settings
        isolated_db = isolated_cache / f"legacy_meta_{id(test_temp_workspace)}.db"
        storage.db_path = isolated_db
        storage._init_db()
        legacy_settings.DB_PATH = isolated_db
        legacy_settings.UPLOAD_DIR = isolated_uploads
        legacy_settings.CACHE_DIR = isolated_cache
    except Exception:
        pass

    yield

    DiskCacheManager.reset_instance()
