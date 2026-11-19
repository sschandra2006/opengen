"""
Optical Prompt Director for Engine 3 (Image Studio).
Enriches raw user briefs with real-world camera optics, lens focal lengths,
studio lighting setups, and negative space geometry to eliminate the "AI plastic sheen".
"""
from typing import Optional, Dict, Any
from opengen.domain.brand import BrandKitSpec


class OpticalPromptDirector:
    """Transforms naive text prompts into photorealistic optical briefs."""

    FOCAL_LENGTH_PRESETS = {
        "product_macro": "shot on Hasselblad H6D-100c with HC 100mm f/2.2 lens at f/5.6, shallow depth of field, creamy bokeh",
        "portrait": "shot on Sony A7R V with G-Master 85mm f/1.4 lens at f/2.0, natural skin micro-texture",
        "environmental": "shot on Leica M11 with Summilux 35mm f/1.4 lens at f/4.0, dynamic wide perspective",
        "standard": "shot on 50mm f/1.8 prime lens, natural human eye perspective, zero barrel distortion"
    }

    LIGHTING_PRESETS = {
        "commercial_studio": "Lighting: Profoto softbox key light at 45-degree angle, subtle cyan rim light on edges, black velvet negative fill",
        "rembrandt": "Lighting: dramatic 45-degree key light creating subtle chiaroscuro and sculpted contours",
        "golden_hour": "Lighting: warm low-sun backlight (3200K) casting soft elongated directional highlights",
        "high_key": "Lighting: diffused dual-bank softbox, clean white bounce fill, perfectly balanced illumination"
    }

    @classmethod
    def expand_prompt(
        cls,
        raw_prompt: str,
        style: str = "photorealistic",
        preset_type: str = "product_macro",
        lighting_type: str = "commercial_studio",
        reserve_negative_space: bool = True,
        brand: Optional[BrandKitSpec] = None
    ) -> str:
        """
        Expands raw user prompt with physical optics, studio lighting,
        and optional 60/40 negative space composition.
        """
        if style in ["vector_illustration", "svg", "minimal"]:
            # For vector/icon styles, enforce clean geometry
            vector_tokens = (
                f"{raw_prompt}. Mathematical clean vector graphic, flat 2D bezier paths, "
                f"smooth curves, SVG styling, crisp iconography, zero raster pixelation, zero noisy gradients."
            )
            if brand:
                vector_tokens += f" Strict brand palette: {brand.colorPalette.primary}, {brand.colorPalette.surfaceCard}."
            return vector_tokens

        optics = cls.FOCAL_LENGTH_PRESETS.get(preset_type, cls.FOCAL_LENGTH_PRESETS["product_macro"])
        lighting = cls.LIGHTING_PRESETS.get(lighting_type, cls.LIGHTING_PRESETS["commercial_studio"])

        # Negative space direction (60/40 rule for commercial typography overlay)
        neg_space = ""
        if reserve_negative_space:
            neg_space = (
                " Composition: rule of thirds with 60% clean negative space on the upper-left canvas "
                "specifically reserved for headline typography overlays, subject positioned in lower right."
            )

        # Brand palette guidance
        brand_tokens = ""
        if brand:
            p = brand.colorPalette
            brand_tokens = (
                f" Harmonious color grade emphasizing brand accents ({p.primary}) and deep backdrop tones ({p.backgroundDark})."
            )

        expanded = (
            f"Commercial photography of {raw_prompt}. "
            f"{optics}. {lighting}. "
            f"Organic micro-textures, zero plastic sheen, realistic surface imperfections, "
            f"ISO 64, 8k resolution, raw color grading.{neg_space}{brand_tokens}"
        )
        return expanded.strip()
