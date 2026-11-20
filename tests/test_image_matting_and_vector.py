"""
Unit and Integration Tests for Image Studio Matting and Vectorization.
Verifies deep background isolation with alpha feathering and offline raster-to-SVG vector tracing.
"""
import pytest
from pathlib import Path
from PIL import Image, ImageDraw
from opengen.engines.image.matting import StudioMattingEngine
from opengen.engines.image.vectorizer import RasterVectorizer
from opengen.engines.image.engine import ImageEngine


@pytest.fixture
def synthetic_product_image(tmp_path):
    """Generates a synthetic product (blue box) on pure white background."""
    img_path = tmp_path / "product_on_white.png"
    img = Image.new("RGBA", (200, 200), (255, 255, 255, 255))
    draw = ImageDraw.Draw(img)
    # Draw a blue centered box
    draw.rectangle([50, 50, 150, 150], fill=(20, 100, 220, 255))
    img.save(str(img_path))
    return str(img_path)


def test_studio_matting_engine_isolation(synthetic_product_image, tmp_path):
    out_isolated = tmp_path / "product_isolated.png"

    res_img = StudioMattingEngine.remove_background(
        image_input=synthetic_product_image,
        output_path=out_isolated,
        edge_feather_radius=1.5
    )

    assert Path(out_isolated).exists()
    assert res_img.mode == "RGBA"

    # Corner pixel should be transparent (alpha == 0)
    corner_pixel = res_img.getpixel((5, 5))
    assert corner_pixel[3] == 0

    # Center pixel should be opaque (alpha > 200)
    center_pixel = res_img.getpixel((100, 100))
    assert center_pixel[3] > 200


def test_raster_vectorizer_svg_generation(synthetic_product_image, tmp_path):
    out_svg = tmp_path / "product.svg"

    svg_content = RasterVectorizer.vectorize_to_svg(
        image_input=synthetic_product_image,
        output_svg_path=out_svg,
        color_hex="#38bdf8"
    )

    assert Path(out_svg).exists()
    assert "<svg" in svg_content
    assert "</svg>" in svg_content
    assert "<path" in svg_content or "<rect" in svg_content
    assert "#38bdf8" in svg_content


def test_image_engine_matting_and_vector_methods(synthetic_product_image, tmp_path):
    engine = ImageEngine()

    # Test isolate_product
    iso_path = tmp_path / "engine_isolated.png"
    res1 = engine.isolate_product(synthetic_product_image, str(iso_path))
    assert Path(res1).exists()

    # Test raster_to_svg
    svg_path = tmp_path / "engine_vector.svg"
    res2 = engine.raster_to_svg(synthetic_product_image, str(svg_path))
    assert Path(svg_path).exists()
    assert "<svg" in Path(res2).read_text(encoding="utf-8")
