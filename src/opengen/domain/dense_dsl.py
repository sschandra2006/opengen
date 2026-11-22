"""
Domain definition for OpenGen Universal Dense Semantic DSL.
Bridges app/modules/token_optimization/dense_parser.py with src/opengen domain architecture.
"""
from app.modules.token_optimization.dense_parser import (
    CatalogItem,
    BentoMetricItem,
    DenseParseResult,
    parse_dense_items,
    parse_dense_items_with_telemetry,
    parse_dense_metrics,
    serialize_dense_items,
    calculate_token_savings,
)

__all__ = [
    "CatalogItem",
    "BentoMetricItem",
    "DenseParseResult",
    "parse_dense_items",
    "parse_dense_items_with_telemetry",
    "parse_dense_metrics",
    "serialize_dense_items",
    "calculate_token_savings",
]
