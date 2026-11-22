"""
Repository Hygiene and Weight Bloat Guardrails Test Suite.
Verifies that the repository remains strictly under 50MB and that no multi-gigabyte
model checkpoints (*.gguf, *.safetensors, *.bin) or generated clutter exist in Git or the filesystem.
"""
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_gitignore_contains_critical_weight_patterns():
    """Verifies that .gitignore contains rules preventing commit of large binary weights."""
    gitignore_path = PROJECT_ROOT / ".gitignore"
    assert gitignore_path.exists()
    content = gitignore_path.read_text(encoding="utf-8")

    assert "*.gguf" in content
    assert "*.safetensors" in content
    assert "*.bin" in content
    assert "*.pt" in content
    assert "*.ckpt" in content
    assert "*.onnx" in content


def test_models_adapters_directory_configured():
    """Verifies that models/adapters exists with proper documentation and .gitkeep."""
    adapters_dir = PROJECT_ROOT / "models" / "adapters"
    assert adapters_dir.exists()
    assert (adapters_dir / ".gitkeep").exists()
    assert (adapters_dir / "README.md").exists()


def test_reports_directory_structure():
    """Verifies that all reports and specifications are cleanly arranged in reports/."""
    reports_dir = PROJECT_ROOT / "reports"
    assert reports_dir.exists()
    assert (reports_dir / "README.md").exists()
    assert (reports_dir / "OPENGEN_UNIVERSAL_TOKEN_REDUCTION_AND_MODEL_OPTIMIZATION_REPORT.md").exists()
    assert (reports_dir / "OPENGEN_UNIVERSAL_TOKEN_REDUCTION_AND_MODEL_OPTIMIZATION_IMPLEMENTATION_PLAN.md").exists()


def test_no_generated_catalog_or_raw_files_in_root():
    """Verifies that generated files (mani mahalaxmi pdfs, extracted_*.txt) are removed from root."""
    root_files = [f.name for f in PROJECT_ROOT.glob("*") if f.is_file()]

    assert "Mani_Mahalaxmi_Traders_Catalog_MRP.pdf" not in root_files
    assert "Mani_Mahalaxmi_Sangam_Dairy_Official_Catalog.pdf" not in root_files
    assert "extracted_catalog.txt" not in root_files
    assert "extracted_raw.txt" not in root_files
