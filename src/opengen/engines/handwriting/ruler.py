"""
Physical Ruled Paper Geometry & Alignment Calculator.
Calibrates sub-millimeter line pitch and margins for direct-to-notebook printing.
"""
from typing import Dict
from opengen.domain.handwriting import RuledPaperSpecs

RULED_PRESETS: Dict[str, RuledPaperSpecs] = {
    "college_ruled": RuledPaperSpecs(
        name="college_ruled",
        line_pitch_mm=7.10,    # Standard College Ruled (0.28 in / 7.1 mm)
        left_margin_mm=31.75,  # 1.25 in left red margin line
        top_margin_mm=25.40,   # 1.0 in top margin
        dpi=300
    ),
    "wide_ruled": RuledPaperSpecs(
        name="wide_ruled",
        line_pitch_mm=8.70,    # Standard Wide Ruled (0.34 in / 8.7 mm)
        left_margin_mm=31.75,
        top_margin_mm=25.40,
        dpi=300
    ),
    "narrow_ruled": RuledPaperSpecs(
        name="narrow_ruled",
        line_pitch_mm=6.35,    # 0.25 in / 6.35 mm
        left_margin_mm=31.75,
        top_margin_mm=25.40,
        dpi=300
    )
}
