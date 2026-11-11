"""
Tests for Engine C: Image & Vector Asset Generation.
Verifies SHA-256 prompt hashing, persistent caching, Pillow composition,
and vector SVG generation.
"""
import pytest
from pathlib import Path
from PIL import Image

from opengen.domain.image import ImageRequest, ImageResponse
from opengen.engines.image.cache import ImageCache
from opengen.engines.image.compositor import ImageCompositor
from opengen.engines.image.providers.recraft_vector import RecraftVectorAdapter
from opengen.engines.image.engine import ImageEngine


def test_image_cache_hashing():
    h1 = ImageCache.compute_hash("A cute cat", "1:1", "photorealistic", "flux")
    h2 = ImageCache.compute_hash("A cute cat", "1:1", "photorealistic", "flux")
    h3 = ImageCache.compute_hash("A cute dog", "1:1", "photorealistic", "flux")

    assert h1 == h2
    assert h1 != h3
    assert len(h1) == 64


def test_recraft_vector_adapter_svg():
    adapter = RecraftVectorAdapter()
    req = ImageRequest(
        prompt="Minimalist cloud architecture icon",
        output_format="svg",
        style="vector"
    )
    raw_bytes, mime_type, cost = adapter.generate(req)
    assert mime_type == "image/svg+xml"
    assert b"<svg" in raw_bytes
    assert b"</svg>" in raw_bytes
    assert cost >= 0.0


def test_image_compositor_transparent_and_aspect():
    # Create test 100x100 white PNG image
    test_img = Image.new("RGB", (100, 100), (255, 255, 255))
    import io
    buf = io.BytesIO()
    test_img.save(buf, format="PNG")
    raw_bytes = buf.getvalue()

    # Process with transparent background
    proc_bytes = ImageCompositor.process_image(raw_bytes, "image/png", transparent_bg=True)
    assert len(proc_bytes) > 0
    with Image.open(io.BytesIO(proc_bytes)) as out_img:
        assert out_img.mode == "RGBA"


def test_image_engine_generate_and_cache(tmp_path):
    engine = ImageEngine()
    req = ImageRequest(
        prompt="Modern logo for AI framework",
        output_format="svg",
        style="vector"
    )
    res = engine.generate_image(req, output_dir=tmp_path)
    assert Path(res.file_path).exists()
    assert res.is_vector is True
    assert res.file_path.endswith(".svg")

    # Second generation of identical prompt should hit cache with 0 cost
    res2 = engine.generate_image(req, output_dir=tmp_path)
    assert res2.provider_used == "cache"
    assert res2.cost_usd == 0.0
