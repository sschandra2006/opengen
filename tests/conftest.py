"""
Pytest configuration and strict test isolation fixtures.
Prevents cross-test pollution and avoids polluting production output/ or cache/ directories
by redirecting BOTH opengen.config.settings and legacy app storage to ephemeral folders.
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
    Redirects live settings instances and caches to ephemeral test workspaces
    per test invocation so tests never pollute production `output/` or `cache/`.
    """
    isolated_cache = test_temp_workspace / "cache"
    isolated_uploads = test_temp_workspace / "uploads"
    isolated_outputs = test_temp_workspace / "output"
    isolated_templates = test_temp_workspace / "templates"
    for p in (isolated_cache, isolated_uploads, isolated_outputs, isolated_templates):
        p.mkdir(parents=True, exist_ok=True)

    monkeypatch.setenv("OPENGEN_CACHE_DIR", str(isolated_cache))
    monkeypatch.setenv("OPENGEN_UPLOAD_DIR", str(isolated_uploads))
    monkeypatch.setenv("OPENGEN_OUTPUT_DIR", str(isolated_outputs))
    monkeypatch.setenv("OPENGEN_DB_PATH", str(isolated_cache / "test_metadata.db"))
    monkeypatch.setenv("OPENGEN_JOBS_DB_PATH", str(isolated_cache / "test_jobs.db"))

    # Mutate live opengen.config.settings singleton using monkeypatch (auto-restored per test!)
    from opengen.config import settings as opengen_settings
    monkeypatch.setattr(opengen_settings, "CACHE_DIR", isolated_cache)
    monkeypatch.setattr(opengen_settings, "UPLOAD_DIR", isolated_uploads)
    monkeypatch.setattr(opengen_settings, "OUTPUT_DIR", isolated_outputs)
    monkeypatch.setattr(opengen_settings, "TEMPLATES_DIR", isolated_templates)
    monkeypatch.setattr(opengen_settings, "DB_PATH", isolated_cache / "test_metadata.db")
    monkeypatch.setattr(opengen_settings, "JOBS_DB_PATH", isolated_cache / "test_jobs.db")

    # Reset cache manager singleton cleanly
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
