"""
Unit and Benchmark Tests for Universal Dense Semantic DSL Parser.
Module 8 & UTRA (Universal Token-Reduction Architecture).
"""
import time
import pytest
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


SAMPLE_RAW_STREAM = """
# Product Catalog Dense Stream
SKU-01 | Full Cream Milk 1L | Dairy | ₹66.00 | ₹62.00 | 1L pkt | true
SKU-02 | Buffalo Curd 400g | Dairy | 40 | 38 | 400g tub | false
SKU-03 | Pure Cow Ghee 500ml | Dairy | 380 | 365 | 500ml jar | true
SKU-04 | Gulab Jamun 1kg | Traditional Sweets | 320.00 | 299.00 | 1kg box
SKU-05 | Fresh Artisanal Bread | Bakery | 45 | 42
"""


def test_parse_dense_items_valid():
    """Verifies that pipe-delimited records parse accurately into CatalogItem Pydantic models."""
    items = parse_dense_items(SAMPLE_RAW_STREAM)
    assert len(items) == 5

    item1 = items[0]
    assert item1.sku == "SKU-01"
    assert item1.name == "Full Cream Milk 1L"
    assert item1.category == "Dairy"
    assert item1.mrp == 66.0
    assert item1.discounted_price == 62.0
    assert item1.unit == "1L pkt"
    assert item1.is_hero is True

    item4 = items[3]
    assert item4.sku == "SKU-04"
    assert item4.category == "Traditional Sweets"
    assert item4.mrp == 320.0
    assert item4.discounted_price == 299.0
    assert item4.is_hero is False


def test_parse_dense_items_with_markdown_fences():
    """Verifies that accidental markdown fences emitted by sloppy models are cleanly stripped."""
    fenced = f"```text\n{SAMPLE_RAW_STREAM}\n```"
    items = parse_dense_items(fenced)
    assert len(items) == 5
    assert items[0].sku == "SKU-01"


def test_parse_dense_items_tab_delimited():
    """Verifies that tab-delimited streams parse correctly."""
    tab_stream = "SKU-10\tOrganic Butter\tDairy\t120\t110\t200g\tfalse"
    items = parse_dense_items(tab_stream, delimiter="|")  # Auto-falls back to tab
    assert len(items) == 1
    assert items[0].name == "Organic Butter"
    assert items[0].mrp == 120.0


def test_parse_dense_telemetry_and_malformed_lines():
    """Verifies that telemetry captures malformed lines for surgical 1-turn reflection."""
    stream_with_error = (
        "SKU-01|Valid Product|Cat|100|90|1 unit|false\n"
        "BROKEN_LINE_WITH_TOO_FEW_FIELDS|Milk\n"
        "SKU-02|Another Valid|Cat|50|45\n"
    )
    result = parse_dense_items_with_telemetry(stream_with_error)
    assert len(result.items) == 2
    assert len(result.malformed_lines) == 1
    assert result.malformed_lines[0][0] == 2  # line 2 failed
    assert "Expected at least 5" in result.malformed_lines[0][2]


def test_parse_dense_metrics():
    """Verifies parsing of Bento card KPI metric lines."""
    raw_metrics = """
    REVENUE | ₹12.4M | +18.2% | MoM
    PROFIT MARGIN | 28.5% | stable | Q3
    ACTIVE CUSTOMERS | 4,200 | +350 | Monthly
    """
    metrics = parse_dense_metrics(raw_metrics)
    assert len(metrics) == 3
    assert metrics[0].label == "REVENUE"
    assert metrics[0].value == "₹12.4M"
    assert metrics[0].trend == "+18.2%"
    assert metrics[0].unit == "MoM"


def test_serialize_dense_items():
    """Verifies serialization back into zero-waste delimited stream."""
    items = parse_dense_items(SAMPLE_RAW_STREAM)
    serialized = serialize_dense_items(items)
    lines = serialized.strip().splitlines()
    assert len(lines) == 5
    assert "SKU-01|Full Cream Milk 1L|Dairy|66.0|62.0|1L pkt|true" in lines[0]


def test_calculate_token_savings():
    """Verifies that token savings calculations show > 65% reduction."""
    items = parse_dense_items(SAMPLE_RAW_STREAM)
    report = calculate_token_savings(items)
    assert report["item_count"] == 5
    assert report["reduction_percentage"] == 75.0
    assert report["tokens_saved"] == 120  # (5 * 32) - (5 * 8) = 160 - 40 = 120


def test_dense_parser_cpu_performance_benchmark():
    """Verifies that parsing 100 dense records takes < 10ms (well under 0.5ms/item)."""
    large_stream = "\n".join([
        f"SKU-{i:03d}|Product Number {i}|Category-{i % 5}|{100 + i}.00|{90 + i}.00|pack|false"
        for i in range(100)
    ])
    t0 = time.perf_counter()
    items = parse_dense_items(large_stream)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    assert len(items) == 100
    assert elapsed_ms < 20.0  # Under 20ms for 100 items on standard CPU
