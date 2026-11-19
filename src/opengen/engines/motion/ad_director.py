"""
Direct-Response Performance Ad Director for Engine 5 (Motion Graphics Studio).
Compiles creative briefs and video audit saliency into high-converting
OpenGen IR v1.1.0 projects strictly capped under 30 seconds.
"""
from typing import Dict, Any, Optional
from opengen.domain.brand import BrandKitSpec
from opengen.engines.motion.models import FootageAuditReport


class AdDirectorAgent:
    """
    Direct-Response Performance Ad Director for OpenGen Engine 5.
    Compiles creative briefs and video audit saliency into high-converting
    OpenGen IR v1.1.0 Projects strictly capped under 30 seconds.
    """

    def __init__(
        self,
        provider_mgr=None,
        target_duration: float = 18.0,
        target_aspect: str = "9:16"
    ):
        self.provider_mgr = provider_mgr
        self.target_duration = min(target_duration, 29.5)
        self.target_aspect = target_aspect

    def build_creative_ad_plan(
        self,
        brief: str,
        audit: Optional[FootageAuditReport] = None,
        brand: Optional[BrandKitSpec] = None,
        target_duration: Optional[float] = None,
        target_aspect: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Synthesizes creative brief and video audit telemetry into an OpenGen IR v1.1.0 Project.
        """
        dur = min(target_duration or self.target_duration, 29.5)
        aspect = target_aspect or self.target_aspect

        best_hook_desc = "Intriguing visual action"
        clip_hook_start = 0.0

        if audit and audit.shots:
            best_hook = audit.top_hook_candidates[0] if audit.top_hook_candidates else audit.shots[0]
            best_hook_desc = best_hook.action_summary
            clip_hook_start = best_hook.start_time

        # Color tokens from brand kit
        bg_dark = brand.colorPalette.backgroundDark if brand else "#090d16"
        card_surface = brand.colorPalette.surfaceCard if brand else "#131b2e"
        accent_color = brand.colorPalette.primary if brand else "#38bdf8"
        brand_name = brand.brandName if brand else "OpenGen"

        words = brief.split()
        hook_headline = " ".join(words[:5]) if words else "STOP SCROLLING"
        agitate_text = " ".join(words[5:12]) if len(words) > 5 else "The Old Manual Method Is Costing You Hours."
        climax_text = " ".join(words[12:20]) if len(words) > 12 else f"{brand_name} Delivers Instant Automation."
        cta_text = f"Try {brand_name} Now"

        # Construct compliant OpenGen IR v1.1.0 Project
        project_ir = {
            "schemaVersion": "1.1.0",
            "projectId": f"proj_ad_{abs(hash(brief)) % 1000000}",
            "title": f"Ad: {hook_headline}",
            "settings": {
                "width": 1080 if aspect == "9:16" else 1920,
                "height": 1920 if aspect == "9:16" else 1080,
                "fps": 30,
                "aspectRatio": aspect,
                "duration": dur,
                "backgroundColor": bg_dark
            },
            "scenes": [
                {
                    "id": "scene_1_hook",
                    "name": "Phase 1: Hook",
                    "start": 0.0,
                    "duration": 2.0,
                    "backgroundColor": bg_dark,
                    "creativeAdDirectives": {
                        "funnelPhase": "hook",
                        "punchIn": {"enabled": True, "scale": 1.25, "focalTarget": "face_eyes"},
                        "audioPunctuation": {"foleyCue": "sub_impact_heavy", "jCutLeadSec": 0.2}
                    },
                    "layers": [
                        {
                            "id": "hook_headline_text",
                            "type": "text",
                            "start": 0.1,
                            "duration": 1.9,
                            "transform": {"x": 540, "y": 600, "scale": 1.0, "opacity": 1.0},
                            "content": {
                                "text": hook_headline.upper(),
                                "fontSize": 78,
                                "fontWeight": 900,
                                "color": "#ffffff",
                                "kineticMode": "word-by-word"
                            }
                        }
                    ]
                },
                {
                    "id": "scene_2_agitate",
                    "name": "Phase 2: Agitate",
                    "start": 2.0,
                    "duration": 3.5,
                    "backgroundColor": card_surface,
                    "creativeAdDirectives": {
                        "funnelPhase": "agitation",
                        "punchIn": {"enabled": False},
                        "audioPunctuation": {"foleyCue": "whoosh_slide", "jCutLeadSec": 0.1}
                    },
                    "layers": [
                        {
                            "id": "agitate_text",
                            "type": "text",
                            "start": 0.2,
                            "duration": 3.3,
                            "transform": {"x": 540, "y": 700, "scale": 1.0, "opacity": 1.0},
                            "content": {
                                "text": agitate_text,
                                "fontSize": 54,
                                "fontWeight": 700,
                                "color": "#94a3b8"
                            }
                        }
                    ]
                },
                {
                    "id": "scene_3_climax",
                    "name": "Phase 3: Climax Payoff",
                    "start": 5.5,
                    "duration": 6.5,
                    "backgroundColor": bg_dark,
                    "creativeAdDirectives": {
                        "funnelPhase": "climax",
                        "punchIn": {"enabled": True, "scale": 1.15},
                        "speedRamp": {"leadIn": 1.8, "reveal": 0.65},
                        "audioPunctuation": {"foleyCue": "riser_tension", "jCutLeadSec": 0.3}
                    },
                    "layers": [
                        {
                            "id": "climax_text",
                            "type": "text",
                            "start": 0.2,
                            "duration": 6.3,
                            "transform": {"x": 540, "y": 650, "scale": 1.0, "opacity": 1.0},
                            "content": {
                                "text": climax_text,
                                "fontSize": 64,
                                "fontWeight": 800,
                                "color": accent_color
                            }
                        }
                    ]
                },
                {
                    "id": "scene_4_cta",
                    "name": "Phase 5: Frictionless CTA",
                    "start": 12.0,
                    "duration": max(2.5, dur - 12.0),
                    "backgroundColor": bg_dark,
                    "creativeAdDirectives": {
                        "funnelPhase": "cta",
                        "punchIn": {"enabled": False},
                        "audioPunctuation": {"foleyCue": "notification_ding", "jCutLeadSec": 0.15}
                    },
                    "layers": [
                        {
                            "id": "cta_button",
                            "type": "text",
                            "start": 0.1,
                            "duration": max(2.4, dur - 12.1),
                            "transform": {"x": 540, "y": 1400, "scale": 1.0, "opacity": 1.0},
                            "content": {
                                "text": cta_text.upper(),
                                "fontSize": 58,
                                "fontWeight": 900,
                                "color": "#ffffff",
                                "pillBackground": accent_color
                            }
                        }
                    ]
                }
            ]
        }

        return project_ir
