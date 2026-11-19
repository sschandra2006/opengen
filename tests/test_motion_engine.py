"""
Unit and Integration Tests for Engine 5 (Motion Graphics Studio).
Verifies the 5-Phase Conversion Funnel, Ad Critic Quality Gate,
Multimodal Footage Saliency, Dynamic 9:16 Smart Reframer, and SDK/API bridges.
"""
import os
import json
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from opengen.client import OpenGenClient
from opengen.engines.motion.engine import MotionEngine
from opengen.engines.motion.ad_director import AdDirectorAgent
from opengen.engines.motion.ad_critic import AdCriticAgent
from opengen.engines.motion.footage_auditor import FootageAuditor
from opengen.engines.motion.smart_reframer import SmartReframer
from opengen.engines.motion.sound_designer import SoundDesigner
from opengen.engines.motion.models import FootageAuditReport
from opengen.domain.brand import BrandKitSpec, ColorPalette
from opengen.api.app import app
from opengen.mcp.server import tool_generate_motion_ad, tool_audit_ad_timeline


@pytest.fixture
def test_video(tmp_path):
    """Creates a short 2-second synthetic MP4 for video test pipelines."""
    out_file = tmp_path / "test_input.mp4"
    import subprocess
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "testsrc=duration=2:size=1280x720:rate=30",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        str(out_file)
    ]
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except Exception:
        out_file.touch()
    return str(out_file)


def test_ad_director_5_phase_funnel():
    director = AdDirectorAgent(target_duration=18.0, target_aspect="9:16")
    plan = director.build_creative_ad_plan(
        brief="Automate document generation with OpenGen Engine 5"
    )

    assert plan["schemaVersion"] == "1.1.0"
    assert plan["settings"]["aspectRatio"] == "9:16"
    assert plan["settings"]["duration"] <= 29.5
    assert len(plan["scenes"]) >= 3

    # Check 5-Phase funnel markers
    hook_scene = plan["scenes"][0]
    assert hook_scene["duration"] <= 2.2
    assert hook_scene["creativeAdDirectives"]["funnelPhase"] == "hook"
    assert hook_scene["creativeAdDirectives"]["punchIn"]["enabled"] is True
    assert hook_scene["creativeAdDirectives"]["audioPunctuation"]["foleyCue"] == "sub_impact_heavy"


def test_ad_critic_audit_and_auto_correction():
    critic = AdCriticAgent()

    # Create a faulty project with hook too slow, no pattern interrupts, and safe-zone breach
    faulty_project = {
        "schemaVersion": "1.1.0",
        "projectId": "faulty_01",
        "settings": {"aspectRatio": "9:16", "duration": 32.0, "height": 1920},
        "scenes": [
            {
                "id": "s1",
                "duration": 4.5,  # Exceeds 2.2s
                "creativeAdDirectives": {},  # Missing punchIn and foley
                "layers": [
                    {"id": "l1", "transform": {"y": 1850}}  # Safe-zone breach (>1680)
                ]
            },
            {
                "id": "s2",
                "duration": 27.5,
                "creativeAdDirectives": {},
                "layers": []
            }
        ]
    }

    audit = critic.audit_ad_timeline(faulty_project)
    assert audit["passed"] is False
    assert len(audit["violations"]) >= 3
    assert any("HOOK_TOO_SLOW" in v for v in audit["violations"])
    assert any("SAFE_ZONE_BREACH" in v for v in audit["violations"])

    # Auto-correct the project
    corrected = critic.auto_correct_timeline(faulty_project, audit)
    new_audit = critic.audit_ad_timeline(corrected)

    assert corrected["scenes"][0]["duration"] <= 2.0
    assert corrected["scenes"][0]["creativeAdDirectives"]["punchIn"]["enabled"] is True
    assert corrected["scenes"][0]["layers"][0]["transform"]["y"] <= 1680


def test_footage_auditor_micro_shots(test_video):
    auditor = FootageAuditor()
    report = auditor.audit_footage(test_video)

    assert isinstance(report, FootageAuditReport)
    assert len(report.shots) >= 1
    assert report.shots[0].hook_score >= 1
    assert report.shots[0].hook_score <= 10


def test_smart_reframer(test_video, tmp_path):
    reframer = SmartReframer()
    out_vertical = tmp_path / "vertical_9x16.mp4"
    res = reframer.reframe_to_vertical(test_video, str(out_vertical))

    assert Path(res).exists()
    assert Path(res).stat().st_size > 0


def test_sound_designer_extraction():
    designer = SoundDesigner()
    dummy_project = {
        "scenes": [
            {
                "start": 0.0,
                "creativeAdDirectives": {
                    "audioPunctuation": {"foleyCue": "sub_impact_heavy", "jCutLeadSec": 0.2}
                }
            },
            {
                "start": 5.0,
                "creativeAdDirectives": {
                    "audioPunctuation": {"foleyCue": "whoosh_slide", "jCutLeadSec": 0.1}
                }
            }
        ]
    }
    cues = designer.extract_sfx_cues_from_project(dummy_project)
    assert len(cues) == 2
    assert cues[0]["sound"] == "sub_impact_heavy"
    assert cues[1]["sound"] == "whoosh_slide"


def test_motion_client_sdk_end_to_end(tmp_path):
    client = OpenGenClient()
    target_mp4 = tmp_path / "sdk_ad.mp4"

    res = client.motion.create_ad(
        brief="Viral motion graphics launch with OpenGen Engine 5",
        duration=15.0,
        output_mp4_path=target_mp4
    )

    assert Path(res.file_path).exists()
    assert res.duration <= 30.0
    assert res.critic_score >= 80
    assert res.job_id is not None

    # Verify persisted job
    job = client.jobs.get(res.job_id)
    assert job is not None
    assert job.engine == "motion"


def test_mcp_motion_tools():
    res = tool_generate_motion_ad("High impact motion trailer", duration=12.0)
    assert res["status"] == "completed"
    assert Path(res["file_path"]).exists()

    timeline_json = json.dumps({
        "scenes": [
            {
                "duration": 1.8,
                "creativeAdDirectives": {
                    "punchIn": {"enabled": True},
                    "audioPunctuation": {"foleyCue": "sub_impact"}
                }
            }
        ]
    })
    audit_res = tool_audit_ad_timeline(timeline_json)
    assert audit_res["status"] == "completed"


def test_rest_api_motion_endpoints():
    tc = TestClient(app)

    # 1. Health check includes motion engine
    h = tc.get("/api/v1/health")
    assert h.status_code == 200
    assert h.json()["engines"]["motion"] == "ready"

    # 2. Generate video ad endpoint
    resp = tc.post("/api/v1/motion/ad", json={
        "brief": "Performance ad for dairy products",
        "duration": 15.0,
        "aspect_ratio": "9:16"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "completed"
    assert Path(data["file_path"]).exists()
    assert data["critic_score"] >= 80
