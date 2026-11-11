"""
Presentation Theme & Typography Presets.
Configures corporate brand palettes, background tints, and typography hierarchy.
"""
from typing import Dict
from opengen.domain.presentation import PresentationThemeSpec

THEMES: Dict[str, PresentationThemeSpec] = {
    "modern_corporate": PresentationThemeSpec(
        name="modern_corporate",
        primary_color="#0F172A",     # Dark Slate
        accent_color="#2563EB",      # Blue
        background_color="#FFFFFF",  # Crisp White
        card_background="#F8FAFC",   # Soft Light Grey
        text_color="#1E293B",
        font_header="Calibri",
        font_body="Calibri"
    ),
    "ocean_blue": PresentationThemeSpec(
        name="ocean_blue",
        primary_color="#0A2540",     # Deep Navy
        accent_color="#00D4B2",      # Teal
        background_color="#FFFFFF",
        card_background="#F4F8FA",
        text_color="#1A202C",
        font_header="Calibri",
        font_body="Calibri"
    ),
    "warm_editorial": PresentationThemeSpec(
        name="warm_editorial",
        primary_color="#1C1917",     # Charcoal
        accent_color="#D97706",      # Amber
        background_color="#FDFBF7",  # Cream
        card_background="#F5F2EB",
        text_color="#292524",
        font_header="Calibri",
        font_body="Calibri"
    ),
    "dark_tech": PresentationThemeSpec(
        name="dark_tech",
        primary_color="#F8FAFC",     # Bright White for dark bg
        accent_color="#8B5CF6",      # Violet
        background_color="#0F172A",  # Dark Background
        card_background="#1E293B",   # Card Surface
        text_color="#CBD5E1",
        font_header="Calibri",
        font_body="Calibri"
    )
}

THEME_REGISTRY = THEMES
