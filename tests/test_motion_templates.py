"""
Tests for Motion Studio Template Registry and Hydration.
"""
from opengen.engines.motion.templates import MotionTemplateRegistry
from opengen.domain.brand import BrandKitSpec, ColorPalette, TypographyTokens


def test_motion_template_listing():
    templates = MotionTemplateRegistry.list_templates()
    assert len(templates) >= 3
    ids = [t["id"] for t in templates]
    assert "flash_sale" in ids
    assert "saas_launch" in ids
    assert "artisan_showcase" in ids


def test_motion_template_hydration():
    brand = BrandKitSpec(
        brandId="brand_artisan",
        brandName="Mani Mahalaxmi Sangam Dairy",
        colorPalette=ColorPalette(primary="#D97706", backgroundDark="#0F172A"),
        typography=TypographyTokens(headingFont="Plus Jakarta Sans")
    )

    ir = MotionTemplateRegistry.hydrate_template(
        template_id="artisan_showcase",
        variables={
            "hook_title": "100% PURE COW GHEE",
            "features": ["Hand-Churned", "Lab-Tested Pure", "Chilled Overnight Delivery"]
        },
        brand=brand,
        aspect_ratio="9:16"
    )

    assert ir["title"] == "Artisan Craft & Heritage Showcase"
    assert ir["settings"]["aspectRatio"] == "9:16"
    assert ir["settings"]["width"] == 1080
    assert ir["settings"]["height"] == 1920
    assert len(ir["scenes"]) == 5
    assert len(ir["foley_cues"]) >= 4

    # Check hook scene
    hook_scene = ir["scenes"][0]
    assert hook_scene["duration"] <= 2.2
    assert any("100% PURE COW GHEE" in str(l.get("content")) for l in hook_scene["layers"])
