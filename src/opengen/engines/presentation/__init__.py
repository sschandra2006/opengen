"""
Engine B: Presentation Generation Engine.
"""
from opengen.engines.presentation.themes import THEMES
from opengen.engines.presentation.layout_solver import CoordinateLayoutSolver
from opengen.engines.presentation.planner import PresentationPlanner
from opengen.engines.presentation.builder import PresentationBuilder
from opengen.engines.presentation.charts import NativeChartBuilder
from opengen.engines.presentation.regenerate import SlideRegenerator
from opengen.engines.presentation.engine import PresentationEngine, presentation_engine

__all__ = [
    "THEMES",
    "CoordinateLayoutSolver",
    "PresentationPlanner",
    "PresentationBuilder",
    "NativeChartBuilder",
    "SlideRegenerator",
    "PresentationEngine",
    "presentation_engine"
]
