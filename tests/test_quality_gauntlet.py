"""
Unit and Integration Tests for the Autonomous G0-G5 Creative Quality Gauntlet.
Verifies schema integrity, hook speeds, mobile 9:16 safe zones, WCAG AA contrast,
monotony limits, audio ducking, and autonomous remediation loops.
"""
import pytest
from opengen.creative.quality_gauntlet import QualityGauntlet, _contrast_ratio
from opengen.creative.quality_gate import CreativeCriticGate


def test_contrast_ratio_calculation():
    # Pure white on dark slate background
    ratio_high = _contrast_ratio("#ffffff", "#090d16")
    assert ratio_high > 15.0

    # Low contrast gray on dark background
    ratio_low = _contrast_ratio("#1e293b", "#090d16")
    assert ratio_low < 3.0


def test_gauntlet_g0_schema_validation():
    # Empty project
    empty_res = QualityGauntlet.evaluate_motion_ir({"scenes": []})
    assert empty_res["passed"] is False
    assert any("G0_SCHEMA_ERROR" in v for v in empty_res["violations"])

    # Invalid schema version
    bad_schema = {
        "schemaVersion": "0.9.0",
        "settings": {"duration": 15.0},
        "scenes": [{"id": "s1", "duration": 1.5, "creativeAdDirectives": {"punchIn": {"enabled": True}, "audioPunctuation": {"foleyCue": "sub_impact_heavy"}}}]
    }
    bad_res = QualityGauntlet.evaluate_motion_ir(bad_schema)
    assert any("G0_SCHEMA_ERROR" in v for v in bad_res["violations"])


def test_gauntlet_g1_hook_and_safe_zone():
    project = {
        "schemaVersion": "1.1.0",
        "settings": {"aspectRatio": "9:16", "width": 1080, "height": 1920, "duration": 18.0},
        "scenes": [
            {
                "id": "s1_hook",
                "duration": 3.0,  # Exceeds 2.2s
                "creativeAdDirectives": {},  # Missing punchIn and foley
                "layers": [
                    {"id": "l_top", "type": "text", "transform": {"y": 50}, "content": {"color": "#ffffff"}},  # Top safe zone breach (<120)
                    {"id": "l_bottom", "type": "shape", "transform": {"y": 1800}}  # Bottom safe zone breach (>1680)
                ]
            }
        ]
    }

    eval_res = QualityGauntlet.evaluate_motion_ir(project)
    assert eval_res["passed"] is False
    assert any("G1_HOOK_VIOLATION" in v for v in eval_res["violations"])
    assert any("G1_SAFE_ZONE_BREACH" in v for v in eval_res["violations"])


def test_gauntlet_g2_contrast_linter():
    project = {
        "schemaVersion": "1.1.0",
        "settings": {"aspectRatio": "9:16", "width": 1080, "height": 1920, "backgroundColor": "#090d16"},
        "scenes": [
            {
                "id": "s1",
                "duration": 1.8,
                "creativeAdDirectives": {"punchIn": {"enabled": True}, "audioPunctuation": {"foleyCue": "whoosh"}},
                "layers": [
                    {"id": "text_dim", "type": "text", "transform": {"y": 500}, "content": {"color": "#121824"}}  # Dark gray on dark blue
                ]
            }
        ]
    }

    eval_res = QualityGauntlet.evaluate_motion_ir(project)
    assert any("G2_CONTRAST_DEFICIT" in v for v in eval_res["violations"])


def test_gauntlet_g4_monotony_and_duration():
    project = {
        "schemaVersion": "1.1.0",
        "settings": {"aspectRatio": "9:16", "duration": 35.0},
        "scenes": [
            {
                "id": "s1_monotonous",
                "duration": 5.0,  # Exceeds 3.8s
                "creativeAdDirectives": {},
                "layers": []
            },
            {
                "id": "s2_long",
                "duration": 30.0,
                "creativeAdDirectives": {},
                "layers": []
            }
        ]
    }

    eval_res = QualityGauntlet.evaluate_motion_ir(project)
    assert any("G4_MONOTONY_CEILING" in v for v in eval_res["violations"])
    assert any("G4_DURATION_OVERRUN" in v for v in eval_res["violations"])


def test_gauntlet_g5_audio_ducking():
    project = {
        "schemaVersion": "1.1.0",
        "settings": {"aspectRatio": "9:16"},
        "scenes": [{"id": "s1", "duration": 2.0, "creativeAdDirectives": {"punchIn": {"enabled": True}, "audioPunctuation": {"foleyCue": "hit"}}}],
        "globalAudio": [
            {"type": "music", "src": "music.mp3", "ducking": False}
        ]
    }

    eval_res = QualityGauntlet.evaluate_motion_ir(project)
    assert any("G5_AUDIO_DUCKING_MISSING" in v for v in eval_res["violations"])


def test_gauntlet_closed_loop_auto_correction():
    flawed_project = {
        "schemaVersion": "1.1.0",
        "settings": {"aspectRatio": "9:16", "width": 1080, "height": 1920, "backgroundColor": "#090d16", "duration": 34.0},
        "scenes": [
            {
                "id": "scene_hook",
                "duration": 3.5,
                "creativeAdDirectives": {},
                "layers": [
                    {"id": "l1", "type": "text", "transform": {"y": 1820}, "content": {"color": "#111827"}}
                ]
            },
            {
                "id": "scene_body",
                "duration": 30.5,
                "creativeAdDirectives": {},
                "layers": []
            }
        ],
        "globalAudio": [
            {"type": "music", "src": "bed.mp3", "ducking": False}
        ]
    }

    initial_eval = QualityGauntlet.evaluate_motion_ir(flawed_project)
    assert initial_eval["passed"] is False

    repaired = QualityGauntlet.auto_correct_motion_ir(flawed_project, initial_eval)
    post_eval = QualityGauntlet.evaluate_motion_ir(repaired)

    # All primary violations should be healed
    assert post_eval["passed"] is True
    assert repaired["scenes"][0]["duration"] <= 2.0
    assert repaired["scenes"][0]["creativeAdDirectives"]["punchIn"]["enabled"] is True
    assert repaired["scenes"][0]["layers"][0]["transform"]["y"] <= 1660
    assert repaired["globalAudio"][0]["ducking"] is True
    assert sum(s["duration"] for s in repaired["scenes"]) < 30.0


def test_creative_critic_gate_exposure():
    assert hasattr(CreativeCriticGate, "gauntlet")
    assert CreativeCriticGate.gauntlet is QualityGauntlet
