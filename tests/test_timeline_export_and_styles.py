"""
Unit and Integration Tests for NLE Timeline Exporter and Expanded Style Archetypes.
Verifies CMX 3600 EDL, Apple FCPXML v1.9 generation, and lemo-opuscar style templates.
"""
import pytest
from pathlib import Path
from opengen.creative.timeline_export import NLETimelineExporter, seconds_to_smpte
from opengen.engines.motion.templates import MotionTemplateRegistry
from opengen.engines.motion.engine import MotionEngine


@pytest.fixture
def sample_project_ir():
    return {
        "schemaVersion": "1.1.0",
        "projectId": "ad_test_nle",
        "title": "QuantumFlow Commercial",
        "settings": {
            "fps": 30,
            "width": 1080,
            "height": 1920,
            "aspectRatio": "9:16",
            "duration": 18.0
        },
        "scenes": [
            {
                "id": "sc_01",
                "name": "Phase 1: Hook",
                "start": 0.0,
                "duration": 2.0,
                "creativeAdDirectives": {"funnelPhase": "hook"}
            },
            {
                "id": "sc_02",
                "name": "Phase 2: Agitate",
                "start": 2.0,
                "duration": 3.0,
                "creativeAdDirectives": {"funnelPhase": "agitation"}
            },
            {
                "id": "sc_03",
                "name": "Phase 3: Solution Climax",
                "start": 5.0,
                "duration": 4.0,
                "creativeAdDirectives": {"funnelPhase": "climax"}
            }
        ]
    }


def test_seconds_to_smpte():
    assert seconds_to_smpte(0.0, 30) == "00:00:00:00"
    assert seconds_to_smpte(1.5, 30) == "00:00:01:15"
    assert seconds_to_smpte(65.0, 30) == "00:01:05:00"


def test_export_cmx3600_edl(sample_project_ir, tmp_path):
    out_edl = tmp_path / "timeline.edl"
    edl_text = NLETimelineExporter.export_cmx3600_edl(sample_project_ir, str(out_edl))

    assert Path(out_edl).exists()
    assert "TITLE: QuantumFlow_Commercial" in edl_text
    assert "FCM: NON-DROP FRAME" in edl_text
    assert "001  AX" in edl_text
    assert "* FROM CLIP NAME: Phase 1: Hook" in edl_text


def test_export_fcpxml(sample_project_ir, tmp_path):
    out_xml = tmp_path / "timeline.fcpxml"
    xml_text = NLETimelineExporter.export_fcpxml(sample_project_ir, str(out_xml))

    assert Path(out_xml).exists()
    assert '<fcpxml version="1.9">' in xml_text
    assert '<format id="r1"' in xml_text
    assert '<clip name="Phase 1: Hook"' in xml_text
    assert '</fcpxml>' in xml_text


def test_expanded_style_archetypes_registry():
    templates = MotionTemplateRegistry.list_templates()
    template_ids = [t["id"] for t in templates]

    assert len(templates) >= 7
    assert "tech_minimalist" in template_ids
    assert "kinetic_velocity" in template_ids
    assert "b2b_explainer" in template_ids
    assert "split_screen_mosaic" in template_ids

    # Hydrate tech_minimalist
    hydrated = MotionTemplateRegistry.hydrate_template("tech_minimalist")
    assert hydrated["schemaVersion"] == "1.1.0"
    assert len(hydrated["scenes"]) >= 3


def test_motion_engine_nle_timeline_methods(sample_project_ir, tmp_path):
    engine = MotionEngine()

    edl_path = tmp_path / "engine.edl"
    res1 = engine.export_timeline_edl(sample_project_ir, str(edl_path))
    assert Path(edl_path).exists()
    assert "001  AX" in res1

    xml_path = tmp_path / "engine.fcpxml"
    res2 = engine.export_timeline_fcpxml(sample_project_ir, str(xml_path))
    assert Path(xml_path).exists()
    assert "<fcpxml" in res2
