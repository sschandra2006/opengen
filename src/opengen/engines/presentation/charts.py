"""
Native Microsoft Excel-backed PowerPoint Chart Builder for Engine B.
Creates native Office charts that remain 100% editable in PowerPoint & Excel.
"""
import logging
from typing import Optional
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

from opengen.domain.presentation import ChartSpec, PresentationThemeSpec

logger = logging.getLogger(__name__)

CHART_TYPE_MAP = {
    "column": XL_CHART_TYPE.COLUMN_CLUSTERED,
    "bar": XL_CHART_TYPE.BAR_CLUSTERED,
    "line": XL_CHART_TYPE.LINE,
    "pie": XL_CHART_TYPE.PIE
}

class NativeChartBuilder:
    """Injects native Excel-backed charts into PowerPoint slides."""

    @classmethod
    def add_chart(
        cls,
        slide,
        chart_spec: ChartSpec,
        x_in: float,
        y_in: float,
        w_in: float,
        h_in: float,
        theme: PresentationThemeSpec
    ):
        chart_data = CategoryChartData()
        chart_data.categories = chart_spec.categories or ["Cat A", "Cat B", "Cat C"]
        values = chart_spec.values or [10.0, 25.0, 15.0]
        chart_data.add_series(chart_spec.series_name, values)

        xl_type = CHART_TYPE_MAP.get(chart_spec.chart_type, XL_CHART_TYPE.COLUMN_CLUSTERED)

        chart_shape = slide.shapes.add_chart(
            xl_type,
            Inches(x_in),
            Inches(y_in),
            Inches(w_in),
            Inches(h_in),
            chart_data
        )

        chart = chart_shape.chart
        chart.has_legend = True
        chart.has_title = bool(chart_spec.title)
        if chart.has_title:
            chart.chart_title.text_frame.text = chart_spec.title
            if chart.chart_title.text_frame.paragraphs:
                chart.chart_title.text_frame.paragraphs[0].font.size = Pt(14)
                chart.chart_title.text_frame.paragraphs[0].font.bold = True

        logger.info(f"Added native {chart_spec.chart_type} chart: '{chart_spec.title}'")
        return chart_shape
