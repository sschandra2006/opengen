"""
Engine D: Pure Realistic Handwriting Generation Engine.
Implements Direct-to-Notebook Printing (100% transparent vector PDF containing ONLY ink)
and High-Resolution 300 DPI Synthetic Scanned Document generation with isolated per-run state.
"""
import logging
import random
from pathlib import Path
from typing import List, Optional, Tuple
from PIL import Image, ImageDraw

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

    def generate_handwriting(
        self,
        text: str,
        output_pdf_path: str,
        transparent_mode: bool = True,
        seed: Optional[int] = None,
    ) -> str:
        """
        Renders handwritten document to PDF (supporting multi-page pagination cleanly).
        If transparent_mode=True: Canvas is 100% transparent RGBA for feeding real physical
        lined notebook paper into a home printer.
        """
        lines = self._wrap_text_to_margins(text) or [""]
        width_px = int(8.5 * self.specs.dpi)
        height_px = int(11.0 * self.specs.dpi)
        start_y = int((self.specs.top_margin_mm / 25.4) * self.specs.dpi)
        max_lines_per_page = max(1, int((height_px - start_y - 100) / self.specs.line_pitch_px))

        # Fresh per-generation simulators so consecutive runs share zero mutable state
        drift_sim = BrownianDriftSimulator(
            baseline_jitter_px=self.profile.baseline_jitter_px,
            char_spacing_noise_px=self.profile.char_spacing_noise_px,
            seed=seed,
        )
        run_rng = random.Random(seed)
        history = {}

        # Split lines cleanly into pages
        page_chunks = [
            lines[i:i + max_lines_per_page]
            for i in range(0, len(lines), max_lines_per_page)
        ]

        canvases: List[Image.Image] = []
        for page_lines in page_chunks:
            if transparent_mode:
                canvas = Image.new("RGBA", (width_px, height_px), (255, 255, 255, 0))
            else:
                canvas = self._create_synthetic_paper(width_px, height_px)

            draw = ImageDraw.Draw(canvas)
            for l_idx, line in enumerate(page_lines):
                drift_sim.reset_line()
                current_x = self.specs.left_margin_px
                baseline_y = start_y + (l_idx * self.specs.line_pitch_px)

                for c_idx, char in enumerate(line):
                    font = self.glyph_bank.get_font_for_char(char, c_idx, history)
                    is_end = (char == " ")
                    dx, dy = drift_sim.get_perturbation(char, is_end_of_word=is_end)
                    ink_color = PenPhysicsSimulator.get_ink_color(
                        pen_type=self.profile.pen_type,
                        is_downstroke=(char in "dfhkltpbqj123456789"),
                        rng=run_rng,
                    )
                    draw.text((current_x + dx, baseline_y + dy), char, font=font, fill=ink_color)
                    char_w = draw.textlength(char, font=font)
                    current_x += char_w + dx

            canvases.append(canvas if transparent_mode else canvas.convert("RGB"))

        out_path = Path(output_pdf_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        canvases[0].save(
            str(out_path),
            "PDF",
            resolution=float(self.specs.dpi),
            save_all=len(canvases) > 1,
            append_images=canvases[1:] if len(canvases) > 1 else [],
        )

        logger.info(f"Handwriting synthesized ({len(canvases)} page(s)) to: {out_path}")
        return str(out_path)

    def _wrap_text_to_margins(self, text: str) -> List[str]:
        max_chars_per_line = int((8.5 * 25.4 - self.specs.left_margin_mm - 20) / 3.0)
        lines: List[str] = []
        for raw_para in text.splitlines() or [""]:
            words = raw_para.split()
            if not words:
                lines.append("")
                continue
            cur_line = []
            cur_len = 0
            for w in words:
                if cur_len + len(w) + 1 > max_chars_per_line and cur_line:
                    lines.append(" ".join(cur_line))
                    cur_line = [w]
                    cur_len = len(w)
                else:
                    cur_line.append(w)
                    cur_len += len(w) + (1 if cur_line[:-1] else 0)
            if cur_line:
                lines.append(" ".join(cur_line))
        return lines

    def _create_synthetic_paper(self, width: int, height: int) -> Image.Image:
        """Draws realistic blue ruled lines and red margin for digital scan mode."""
        canvas = Image.new("RGBA", (width, height), (252, 252, 250, 255))
        draw = ImageDraw.Draw(canvas)

        start_y = int((self.specs.top_margin_mm / 25.4) * self.specs.dpi)
        left_m = self.specs.left_margin_px

        curr_y = start_y
        while curr_y < (height - 80):
            draw.line([(0, curr_y), (width, curr_y)], fill=(195, 220, 245, 180), width=2)
            curr_y += self.specs.line_pitch_px

        draw.line([(left_m - 15, 0), (left_m - 15, height)], fill=(245, 175, 175, 200), width=2)
        return canvas


handwriting_engine = HandwritingEngine()
