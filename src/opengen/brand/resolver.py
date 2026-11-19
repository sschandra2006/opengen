"""
Cross-Studio Brand Kit Token Resolver.
Transforms BrandKitSpec design tokens into engine-specific formats:
- Typst variables for Engine 1 (Document Studio)
- CSS custom properties and PresentationThemeSpec for Engine 2 (Presentation Studio)
- Optical prompt token strings and hex constraints for Engine 3 (Image Studio)
"""
from typing import Dict, Any, Optional
from opengen.domain.brand import BrandKitSpec
from opengen.domain.presentation import PresentationThemeSpec


class BrandKitTokenResolver:
    """Translates high-level brand kit design tokens to target rendering formats."""

    @classmethod
    def to_typst_vars(cls, brand: BrandKitSpec) -> str:
        """Emits Typst variable definitions for compilation."""
        p = brand.colorPalette
        t = brand.typography
        g = brand.geometry
        return f"""
        // OpenGen Brand Kit Tokens: {brand.brandName} ({brand.brandId})
        #let brand-name = "{brand.brandName}"
        #let brand-primary = rgb("{p.primary}")
        #let brand-secondary = rgb("{p.secondary}")
        #let brand-bg-dark = rgb("{p.backgroundDark}")
        #let brand-bg-light = rgb("{p.backgroundLight}")
        #let brand-surface = rgb("{p.surfaceCard}")
        #let brand-surface-light = rgb("{p.surfaceCardLight}")
        #let brand-text = rgb("{p.textHighContrast}")
        #let brand-text-dark = rgb("{p.textDark}")
        #let brand-text-muted = rgb("{p.textMuted}")
        #let brand-success = rgb("{p.accentSuccess}")
        #let brand-warning = rgb("{p.accentWarning}")
        #let brand-border = rgb("{p.borderSubtle}")
        #let font-display = "{t.displayFont}"
        #let font-heading = "{t.headingFont}"
        #let font-body = "{t.bodyFont}"
        #let font-code = "{t.codeFont}"
        #let card-radius = {g.cardCornerRadiusPx}pt
        """

    @classmethod
    def to_css_variables(cls, brand: BrandKitSpec) -> str:
        """Emits CSS custom properties for web and Bento HTML slides."""
        p = brand.colorPalette
        t = brand.typography
        g = brand.geometry
        return f"""
        :root {{
          --brand-primary: {p.primary};
          --brand-secondary: {p.secondary};
          --brand-bg-dark: {p.backgroundDark};
          --brand-bg-light: {p.backgroundLight};
          --brand-surface-card: {p.surfaceCard};
          --brand-surface-card-light: {p.surfaceCardLight};
          --brand-text-high: {p.textHighContrast};
          --brand-text-muted: {p.textMuted};
          --brand-text-dark: {p.textDark};
          --brand-accent-success: {p.accentSuccess};
          --brand-accent-warning: {p.accentWarning};
          --brand-border: {p.borderSubtle};
          --font-display: '{t.displayFont}', serif;
          --font-heading: '{t.headingFont}', sans-serif;
          --font-body: '{t.bodyFont}', sans-serif;
          --font-code: '{t.codeFont}', monospace;
          --card-radius: {g.cardCornerRadiusPx}px;
          --button-radius: {g.buttonCornerRadiusPx}px;
          --shadow-elevation: {g.shadowElevation};
        }}
        """

    @classmethod
    def to_presentation_theme(cls, brand: BrandKitSpec) -> PresentationThemeSpec:
        """Converts BrandKit to a native PPTX PresentationThemeSpec."""
        p = brand.colorPalette
        t = brand.typography
        return PresentationThemeSpec(
            name=brand.brandId,
            primary_color=p.textHighContrast if p.backgroundDark == "#090d16" else p.primary,
            accent_color=p.primary,
            background_color=p.backgroundDark,
            card_background=p.surfaceCard,
            text_color=p.textMuted,
            font_header=t.headingFont,
            font_body=t.bodyFont
        )

    @classmethod
    def to_optical_prompt_tokens(cls, brand: BrandKitSpec) -> str:
        """Generates photographic prompt style tokens to enforce brand palette."""
        p = brand.colorPalette
        return (
            f"Color grading palette inspired by {brand.brandName}: "
            f"primary accents ({p.primary}), deep background tones ({p.backgroundDark}), "
            f"clean studio card surfaces ({p.surfaceCard}), high contrast highlights ({p.textHighContrast}). "
            f"Strict brand consistency, zero fluorescent oversaturation."
        )

    @classmethod
    def to_motion_tokens(cls, brand: BrandKitSpec) -> Dict[str, Any]:
        """Translates brand tokens into motion design directives for Engine 5."""
        p = brand.colorPalette
        t = brand.typography
        g = brand.geometry
        return {
            "backgroundColor": p.backgroundDark,
            "surfaceColor": p.surfaceCard,
            "accentColor": p.primary,
            "textColor": p.textHighContrast,
            "mutedColor": p.textMuted,
            "cardCornerRadius": g.cardCornerRadiusPx,
            "fontHeading": t.headingFont,
            "fontDisplay": t.displayFont,
            "easing": "cubic-bezier(0.16, 1, 0.3, 1)",
            "safeZoneMarginPx": 240
        }

    @classmethod
    def to_handwriting_profile(cls, brand: BrandKitSpec) -> Dict[str, Any]:
        """Maps brand design tone to handwriting physical instrument properties."""
        p = brand.colorPalette
        return {
            "pen_type": "fountain_pen" if "heritage" in brand.brandName.lower() or "dairy" in brand.brandName.lower() else "ballpoint_blue",
            "paper_mode": "direct_print_transparent",
            "primary_ink_rgb": p.textHighContrast
        }
