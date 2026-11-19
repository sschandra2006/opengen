"""
Domain models for Cross-Studio Brand Kits and Unified Design Tokens.
Enforces shared typography, 60-30-10 color palettes, geometry, and asset DNA across
Engine 1 (Documents), Engine 2 (Presentations), Engine 3 (Images), and Motion Graphics.
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class ColorPalette(BaseModel):
    """
    60-30-10 Brand Color Palette.
    60% dominant base, 30% structural card surfaces, 10% high-impact accent.
    """
    primary: str = "#38bdf8"             # Primary accent (e.g. Sky 400)
    secondary: str = "#6366f1"           # Secondary accent (e.g. Indigo 500)
    backgroundDark: str = "#090d16"      # 60% dominant dark base
    backgroundLight: str = "#f8fafc"     # 60% dominant light base
    surfaceCard: str = "#131b2e"         # 30% card surface container
    surfaceCardLight: str = "#ffffff"    # 30% light card container
    textHighContrast: str = "#ffffff"    # High legibility header text
    textMuted: str = "#94a3b8"           # Muted secondary / subtitle text
    textDark: str = "#0f172a"            # Dark text for light mode
    accentSuccess: str = "#10b981"       # Positive / growth indicator
    accentWarning: str = "#f59e0b"       # Attention indicator
    borderSubtle: str = "#1e293b"        # Structural card borders


class TypographyTokens(BaseModel):
    """Swiss Editorial and Enterprise Typography Tokens."""
    displayFont: str = "Newsreader"      # Editorial Display Serif
    headingFont: str = "Plus Jakarta Sans" # Modern Geometric Sans
    bodyFont: str = "Inter"              # High-legibility neutral body sans
    codeFont: str = "JetBrains Mono"     # Monospace for tabular data & code
    modularRatio: float = 1.25           # Major Third scale ratio


class GeometryTokens(BaseModel):
    """Component corner radius and elevation tokens."""
    cardCornerRadiusPx: int = 12
    buttonCornerRadiusPx: int = 8
    borderWidthPx: int = 1
    shadowElevation: str = "0 8px 30px rgba(0, 0, 0, 0.12)"


class AssetTokens(BaseModel):
    """Canonical vector and image brand marks."""
    logoSvg: Optional[str] = None
    logoMarkPng: Optional[str] = None
    soundmarkAudio: Optional[str] = None


class BrandKitSpec(BaseModel):
    """Complete Cross-Studio Brand Kit Definition."""
    brandId: str
    brandName: str
    colorPalette: ColorPalette = Field(default_factory=ColorPalette)
    typography: TypographyTokens = Field(default_factory=TypographyTokens)
    geometry: GeometryTokens = Field(default_factory=GeometryTokens)
    assets: AssetTokens = Field(default_factory=AssetTokens)
    metadata: Dict[str, Any] = Field(default_factory=dict)
