"""
Unit and Integration Tests for Document and Presentation Deep Bridges.
Verifies reference-to-Typst automated catalog compilation and Marp/Slidev Markdown deck generation.
"""
import pytest
from pathlib import Path
from opengen.engines.document.engine import DocumentEngine
from opengen.engines.presentation.engine import PresentationEngine
from opengen.engines.presentation.marp_compiler import MarpSlideCompiler
from opengen.domain.brand import BrandKitSpec, ColorPalette, TypographyTokens


@pytest.fixture
def synthetic_reference_pdf(tmp_path):
    """Creates a simple synthetic PDF catalog with product rows for extraction testing."""
    pdf_path = tmp_path / "reference_catalog.pdf"
    import pymupdf as fitz
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 72), "Official Sangam Dairy Price Guide\n\nPure Vedic Ghee 1L - ₹1,450\nCultured Butter 500g - ₹450\nFresh Buffalo Milk 1L - ₹85\nMalai Paneer 200g - ₹120\n", fontsize=14)
    doc.save(str(pdf_path))
    doc.close()
    return str(pdf_path)


def test_compile_reference_to_typst_catalog(synthetic_reference_pdf, tmp_path):
    out_pdf = tmp_path / "compiled_typst_catalog.pdf"

    res_pdf = DocumentEngine.compile_reference_to_typst_catalog(
        reference_pdf_path=synthetic_reference_pdf,
        output_pdf_path=str(out_pdf),
        title="Sangam Dairy Wholesale Price Guide",
        hero_ratio=0.25
    )

    assert Path(res_pdf).exists()
    assert Path(res_pdf).stat().st_size > 1000

    # Verify Typst markup was generated
    typ_file = out_pdf.with_suffix(".typ")
    assert typ_file.exists()
    typ_content = typ_file.read_text(encoding="utf-8")
    assert "Sangam Dairy Wholesale Price Guide" in typ_content
    assert "HERO SPOTLIGHT" in typ_content


def test_marp_presentation_compiler(tmp_path):
    engine = PresentationEngine()
    out_md = tmp_path / "bento_deck.md"

    deck, res_md = engine.compile_marp_presentation(
        topic="OpenGen Multi-Modal Generative Framework",
        output_md_path=str(out_md),
        slide_count=5
    )

    assert Path(res_md).exists()
    md_text = Path(res_md).read_text(encoding="utf-8")
    assert "marp: true" in md_text
    assert "theme: gaia" in md_text
    assert "# " in md_text
    assert '<div class="card">' in md_text
    assert len(deck.slides) == 5
