"""
Engine D: Pure Realistic Handwriting Generation Engine.
Implements Direct-to-Notebook Printing (100% transparent vector PDF containing ONLY ink)
and High-Resolution 300 DPI Synthetic Scanned Document generation.
"""
import io
import logging
from pathlib import Path
from typing import List, Optional
from PIL import Image, ImageDraw, ImageFont

from opengen.config import settings
from opengen.domain.handwriting import RuledPaperSpecs, HandwritingProfile
from opengen.engines.handwriting.ruler import RULED_PRESETS
from opengen.engines.handwriting.glyph_bank import GlyphVariantBank
from opengen.engines.handwriting.drift import BrownianDriftSimulator
from opengen.engines.handwriting.physics import PenPhysicsSimulator

logger = logging.getLogger(__name__)

class HandwritingEngine:
    """Master generation engine for realistic handwriting synthesis."""

    def __init__(
        self,
        specs: Optional[RuledPaperSpecs] = None,
        profile: Optional[HandwritingProfile] = None
    ):
        self.specs = specs or RULED_PRESETS["college_ruled"]
        self.profile = profile or HandwritingProfile()
        self.glyph_bank = GlyphVariantBank(font_size=int(self.specs.line_pitch_px * 0.75))
        self.drift_sim = BrownianDriftSimulator()

    def generate_handwriting(
        self,
        text: str,
        output_pdf_path: str,
        transparent_mode: bool = True
    ) -> str:
        """
        Renders handwritten document to PDF.
        If transparent_mode=True: Canvas is 100% transparent RGBA for feeding real physical
        lined notebook paper into a home printer.
        """
        lines = self._wrap_text_to_margins(text)
        width_px = int((8.5 * self.specs.dpi))
        height_px = int((11.0 * self.specs.dpi))

        # 1. Canvas setup
        if transparent_mode:
            canvas = Image.new("RGBA", (width_px, height_px), (255, 255, 255, 0))
        else:
            canvas = self._create_synthetic_paper(width_px, height_px)

        draw = ImageDraw.Draw(canvas)
        start_y = int((self.specs.top_margin_mm / 25.4) * self.specs.dpi)
        history = {}

        max_lines_per_page = int((height_px - start_y - 100) / self.specs.line_pitch_px)
        page_lines = lines[:max_lines_per_page]

        # 2. Render line by line
        for l_idx, line in enumerate(page_lines):
            self.drift_sim.reset_line()
            current_x = self.specs.left_margin_px
            baseline_y = start_y + (l_idx * self.specs.line_pitch_px)

            for c_idx, char in enumerate(line):
                font = self.glyph_bank.get_font_for_char(char, c_idx, history)
                is_end = (char == " ")
                dx, dy = self.drift_sim.get_perturbation(char, is_end_of_word=is_end)
                ink_color = PenPhysicsSimulator.get_ink_color(
                    pen_type=self.profile.pen_type,
                    is_downstroke=(char in "dfhkltpbqj123456789")
                )

                draw.text((current_x + dx, baseline_y + dy), char, font=font, fill=ink_color)
                char_w = draw.textlength(char, font=font)
                current_x += char_w + dx

        # 3. Export to PDF
        out_path = Path(output_pdf_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        if transparent_mode:
            # Save RGBA directly to PNG or transparent PDF
            canvas.save(str(out_path), "PDF", resolution=float(self.specs.dpi))
        else:
            rgb_canvas = canvas.convert("RGB")
            rgb_canvas.save(str(out_path), "PDF", resolution=float(self.specs.dpi))

        logger.info(f"Handwriting synthesized to: {output_pdf_path}")
        return str(out_path)

    def _wrap_text_to_margins(self, text: str) -> List[str]:
        max_chars_per_line = int((8.5 * 25.4 - self.specs.left_margin_mm - 20) / 3.0)
        words = text.split()
        lines = []
        cur_line = []
        cur_len = 0

        for w in words:
            if cur_len + len(w) + 1 > max_chars_per_line:
                lines.append(" ".join(cur_line))
                cur_line = [w]
                cur_len = len(w)
            else:
                cur_line.append(w)
                cur_len += len(w) + 1

        if cur_line:
            lines.append(" ".join(cur_line))
        return lines

    def _create_synthetic_paper(self, width: int, height: int) -> Image.Image:
        """Draws realistic blue ruled lines and red margin for digital scan mode."""
        canvas = Image.new("RGBA", (width, height), (252, 252, 250, 255))
        draw = ImageDraw.Draw(canvas)

        start_y = int((self.specs.top_margin_mm / 25.4) * self.specs.dpi)
        left_m = self.specs.left_margin_px

        # Horizontal blue ruled lines
        curr_y = start_y
        while curr_y < (height - 80):
            draw.line([(0, curr_y), (width, curr_y)], fill=(195, 220, 245, 180), width=2)
            curr_y += self.specs.line_pitch_px

        # Vertical red margin line
        draw.line([(left_m - 15, 0), (left_m - 15, height)], fill=(245, 175, 175, 200), width=2)
        return canvas

handwriting_engine = HandwritingEngine()
