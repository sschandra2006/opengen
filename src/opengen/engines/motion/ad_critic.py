"""
Autonomous Pre-Flight Ad Quality Gate for Engine 5 (Motion Graphics Studio).
Evaluates compiled project IRs against social retention metrics before rendering,
and applies automatic remediations.
"""
from typing import Dict, Any, List, Optional
from opengen.engines.motion.models import AdCriticResult


class AdCriticAgent:
    """
    Autonomous Pre-Flight Ad Quality Gate for OpenGen Engine 5.
    Evaluates compiled project IRs against social retention metrics *before* rendering.
    Flags hook sluggishness, visual monotony, duration overruns, and UI safe-zone collisions.
    """

    def audit_ad_timeline(self, project_ir: Dict[str, Any]) -> Dict[str, Any]:
        """Audits an OpenGen IR v1.1.0 project against short-form retention criteria."""
        violations: List[str] = []
        scenes = project_ir.get("scenes", [])

        if not scenes:
            return {
                "passed": False,
                "score": 0,
                "violations": ["EMPTY_PROJECT: Project contains no scenes."],
                "suggestedRemedies": ["Add at least 3 scenes complying with the 5-phase conversion funnel."]
            }

        # 1. Hook Speed Check (0-2s)
        first_scene = scenes[0]
        if first_scene.get("duration", 0) > 2.2:
            violations.append(f"HOOK_TOO_SLOW: Scene 1 duration ({first_scene.get('duration')}s) exceeds 2.2s.")

        first_scene_directives = first_scene.get("creativeAdDirectives") or {}
        has_first_punch = first_scene_directives.get("punchIn", {}).get("enabled", False)
        has_first_foley = bool(first_scene_directives.get("audioPunctuation", {}).get("foleyCue"))
        if not has_first_punch and not has_first_foley:
            violations.append("HOOK_LACKS_INTERRUPT: Scene 1 lacks a pattern interrupt (punch-in or foley cue).")

        # 2. Visual Monotony Check
        for scene in scenes:
            dur = scene.get("duration", 0)
            directives = scene.get("creativeAdDirectives") or {}
            has_punch = directives.get("punchIn", {}).get("enabled", False)
            if dur > 3.8 and not has_punch:
                violations.append(f"SCENE_MONOTONY: Scene '{scene.get('id')}' duration ({dur}s) exceeds 3.8s without dynamic punch-in.")

        # 3. Overall Duration Cap (< 30.0s)
        total_duration = sum(s.get("duration", 0) for s in scenes)
        if total_duration >= 30.0:
            violations.append(f"DURATION_OVERRUN: Total duration ({total_duration:.1f}s) exceeds 30.0s ad limit.")

        # 4. Safe-Zone Violations (9:16 mobile UI overlays)
        settings = project_ir.get("settings", {})
        if settings.get("aspectRatio") == "9:16":
            height = settings.get("height", 1920)
            for scene in scenes:
                for layer in scene.get("layers", []):
                    transform = layer.get("transform") or {}
                    y_pos = transform.get("y", 0)
                    if y_pos > (height - 240):
                        violations.append(
                            f"SAFE_ZONE_BREACH: Layer '{layer.get('id')}' in scene '{scene.get('id')}' "
                            f"at y={y_pos} encroaches on TikTok/Reels bottom UI safe margin."
                        )

        passed = len(violations) == 0
        score = max(0, 100 - (len(violations) * 20))

        remedies = []
        if not passed:
            for v in violations:
                if "HOOK_TOO_SLOW" in v:
                    remedies.append("Trim opening hook scene to <= 2.0s.")
                elif "HOOK_LACKS_INTERRUPT" in v:
                    remedies.append("Inject a 1.25x scale punch-in or 'sub_impact_heavy' SFX at t=0s.")
                elif "SCENE_MONOTONY" in v:
                    remedies.append("Divide static scene or add digital punch-in scale tween.")
                elif "DURATION_OVERRUN" in v:
                    remedies.append("Accelerate scene pacing to cap total duration under 29.5s.")
                elif "SAFE_ZONE_BREACH" in v:
                    remedies.append("Shift bottom layers up by at least 260px from bottom edge.")

        return {
            "passed": passed,
            "score": score,
            "violations": violations,
            "suggestedRemedies": remedies
        }

    def auto_correct_timeline(self, project_ir: Dict[str, Any], audit_result: Dict[str, Any]) -> Dict[str, Any]:
        """Applies automatic corrections to repair violations identified by the audit."""
        import copy
        corrected = copy.deepcopy(project_ir)
        scenes = corrected.get("scenes", [])
        if not scenes:
            return corrected

        # Fix 1: Hook too slow
        if scenes[0].get("duration", 0) > 2.0:
            diff = scenes[0]["duration"] - 2.0
            scenes[0]["duration"] = 2.0
            for s in scenes[1:]:
                s["start"] = max(0.0, s.get("start", 0.0) - diff)

        # Fix 2: Hook lacks pattern interrupt
        if not scenes[0].get("creativeAdDirectives"):
            scenes[0]["creativeAdDirectives"] = {}
        s0_dir = scenes[0]["creativeAdDirectives"]
        if not s0_dir.get("punchIn", {}).get("enabled"):
            s0_dir["punchIn"] = {"enabled": True, "scale": 1.25, "focalTarget": "face_eyes"}
        if not s0_dir.get("audioPunctuation", {}).get("foleyCue"):
            s0_dir["audioPunctuation"] = {"foleyCue": "sub_impact_heavy", "jCutLeadSec": 0.2}

        # Fix 3: Safe zone breaches
        height = corrected.get("settings", {}).get("height", 1920)
        for scene in scenes:
            for layer in scene.get("layers", []):
                if not layer.get("transform"):
                    layer["transform"] = {}
                t = layer["transform"]
                if t.get("y", 0) > (height - 240):
                    t["y"] = height - 320

        # Fix 4: Total duration cap
        total = sum(s.get("duration", 0) for s in scenes)
        if total >= 30.0:
            factor = 28.0 / total
            curr_start = 0.0
            for s in scenes:
                s["start"] = curr_start
                s["duration"] = round(s["duration"] * factor, 2)
                curr_start += s["duration"]
            corrected["settings"]["duration"] = 28.0

        return corrected
