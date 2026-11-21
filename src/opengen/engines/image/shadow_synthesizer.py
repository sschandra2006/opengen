"""
Studio Relighting and Contact Shadow Synthesizer for Engine 3 (Image Studio).
Implements dual-pass physical contact shadow & directional cast shadow synthesis
under transparent product plates over lifestyle backgrounds.
"""
import logging
from pathlib import Path
from typing import Optional, Tuple
import numpy as np
from PIL import Image, ImageFilter, ImageOps

logger = logging.getLogger(__name__)


class StudioShadowSynthesizer:
    """Synthesizes physics-based contact shadows and directional cast shadows."""

    @staticmethod
    def composite_product_with_contact_shadow(
        product_png_path: str,
        background_jpg_path: str,
        output_path: str,
        light_angle_deg: float = 45.0,
        shadow_intensity: float = 0.65,
        offset_distance_px: int = 24,
        scale_product: float = 0.85
    ) -> str:
        """
        Synthesizes dual-pass physical contact shadow & directional cast shadow
        beneath an isolated product cutout over a lifestyle background.

        Physics Equation:
        Cast shadow opacity S(d) decays with distance, blur sigma(d) expands:
        sigma(d) = sigma_0 + k * d, S(d) = S_max * e^(-lambda * d)
        """
        product = Image.open(product_png_path).convert("RGBA")
        background = Image.open(background_jpg_path).convert("RGBA")

        # Resize product if desired to fit background nicely
        bg_w, bg_h = background.size
        p_w, p_h = product.size
        target_w = int(bg_w * scale_product)
        target_h = int(p_h * (target_w / p_w))
        if target_h > int(bg_h * 0.9):
            target_h = int(bg_h * 0.85)
            target_w = int(p_w * (target_h / p_h))
        product = product.resize((target_w, target_h), Image.Resampling.LANCZOS)

        # 1. Extract or compute alpha mask of product
        alpha = product.split()[3]
        # If alpha is completely opaque, extract mask using near-white luminance
        if alpha.getextrema() == (255, 255):
            gray = ImageOps.grayscale(product)
            alpha = gray.point(lambda p: 0 if p > 240 else 255)

        # 2. Hard Ambient Occlusion (AO) Contact Shadow (anchors product to surface, preventing "floating")
        # sigma_0 = 2px, high opacity (0.85-0.90), tight vertical anchor (3px)
        contact_sigma = max(1.5, float(scale_product * 2.0))
        contact_mask = alpha.filter(ImageFilter.GaussianBlur(radius=contact_sigma))
        contact_shadow = Image.new(
            "RGBA", product.size,
            (0, 0, 0, int(255 * min(0.95, shadow_intensity * 0.90)))
        )

        # 3. Soft Directional Cast Shadow with Physical Distance Decay
        # sigma(d) = sigma_0 + k * d, S(d) = S_max * exp(-lambda * d)
        d = float(offset_distance_px)
        cast_sigma = max(6.0, 2.0 + 0.65 * d)
        cast_decay = float(np.exp(-0.018 * d))
        cast_opacity = min(1.0, shadow_intensity * 0.55 * cast_decay)

        rad = np.radians(light_angle_deg)
        offset_x = int(d * np.cos(rad))
        offset_y = int(d * 1.3 * np.sin(rad))

        cast_mask = alpha.filter(ImageFilter.GaussianBlur(radius=cast_sigma))
        cast_shadow = Image.new(
            "RGBA", product.size,
            (0, 0, 0, int(255 * cast_opacity))
        )

        # Calculate centering coordinates on background
        pos_x = (bg_w - target_w) // 2
        pos_y = (bg_h - target_h) // 2 + int(bg_h * 0.05)

        # 4. Multi-layer compositing
        final_canvas = background.copy()

        # Step A: Directional Cast Shadow (soft background falloff)
        final_canvas.paste(cast_shadow, (pos_x + offset_x, pos_y + offset_y), mask=cast_mask)

        # Step B: Hard Contact Shadow (prevents floating product)
        final_canvas.paste(contact_shadow, (pos_x, pos_y + 4), mask=contact_mask)

        # Step C: Crisp Product Plate
        final_canvas.paste(product, (pos_x, pos_y), mask=alpha)

        # Step D: Save output artifact
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        final_canvas.convert("RGB").save(str(out_file), "JPEG", quality=95)
        logger.info(f"Studio product composite with contact shadow saved to: {output_path}")
        return str(out_file)
