"""
OpenGen: Modular, Open-Source, Self-Hostable AI Generation Framework.
Supports Documents (DOCX/PDF), Presentations (PPTX), Images (Raster/Vector SVG),
and Realistic Handwriting Synthesis.
"""

from opengen.client import (
    OpenGenClient,
    DocumentResult,
    PresentationResult,
    ImageResult,
    HandwritingResult,
)
from opengen.config import settings

__version__ = "1.0.0"
__author__ = "OpenGen Maintainers"
__license__ = "Apache-2.0"

__all__ = [
    "OpenGenClient",
    "DocumentResult",
    "PresentationResult",
    "ImageResult",
    "HandwritingResult",
    "settings",
    "__version__",
]
