"""
Motion Template Registry & Variable Hydrator for Engine 5 (Motion Graphics Studio).
Provides pre-designed high-converting motion ad archetypes adhering to the 5-phase funnel:
- Direct-Response Flash Sale (<20s)
- SaaS Product Launch & Feature Blitz (<25s)
- Artisan Catalog Showcase (<22s)
- Minimalist Quote / Audiogram (<15s)
"""
from typing import Dict, Any, List, Optional
from opengen.engines.motion.models import (
    MotionProjectIR, MotionScene, MotionLayer, LayerAnimation, FoleyCue, ProjectSettings
)
from opengen.domain.brand import BrandKitSpec


class MotionTemplateRegistry:
    """Pre-configured ad blueprints hydrated with custom copy and brand tokens."""

    TEMPLATES: Dict[str, Dict[str, Any]] = {
        "flash_sale": {
            "name": "Direct-Response Flash Sale",
            "aspect_ratio": "9:16",
            "duration": 18.0,
            "description": "High-urgency promotional ad with 1.8s punchy hook, feature blitz, and discount CTA.",
            "default_vars": {
                "hook_title": "WAIT. STOP SCROLLING.",
                "hook_subtitle": "This 48-Hour Secret Drops Right Now",
                "problem": "Tired of overpaying for generic quality?",
                "solution": "Meet the Handcrafted Pure Standard",
                "features": ["100% Organic", "Zero Fillers", "Overnight Chilled Delivery"],
                "cta_text": "CLAIM 40% OFF TODAY",
                "cta_url": "sangamdairy.com/deal"
            }
        },
        "saas_launch": {
            "name": "SaaS Product Launch & Velocity",
            "aspect_ratio": "16:9",
            "duration": 22.0,
            "description": "Sleek B2B product walkthrough with dark mode bento cards, UI popouts, and metric milestones.",
            "default_vars": {
                "hook_title": "The Old Way of Document Generation is Dead",
                "hook_subtitle": "Meet OpenGen 2.0: 5 Engines, Zero Compromise",
                "problem": "Disconnected tools produce slow, disjointed, plastic AI content.",
                "solution": "One Unified Creative Director with Typst, Bento, and Video",
                "features": ["<30ms Typst Speed", "12-Col Bento Layouts", "Tri-Tier Audio Foley"],
                "cta_text": "START BUILDING FREE",
                "cta_url": "opengen.dev"
            }
        },
        "artisan_showcase": {
            "name": "Artisan Craft & Heritage Showcase",
            "aspect_ratio": "9:16",
            "duration": 20.0,
            "description": "Organic, warm editorial pace for luxury food, dairy, and handcrafted retail.",
            "default_vars": {
                "hook_title": "Purity You Can Taste",
                "hook_subtitle": "Traditional Bilona Churning in Brass Vessels",
                "problem": "Factory butter and refined oils stripped of natural vitamins.",
                "solution": "Pure Vedic Ghee Crafted in Small Farm Batches",
                "features": ["Single-Origin Gir Cow A2 Milk", "Cultured Curd Churned", "Lab-Certified Pure"],
                "cta_text": "ORDER FARM-FRESH GHEE",
                "cta_url": "sangamdairy.com/ghee"
            }
        }
    }

    @classmethod
    def list_templates(cls) -> List[Dict[str, Any]]:
        """Lists available template identifiers and summaries."""
        return [
            {
                "id": k,
                "name": v["name"],
                "aspect_ratio": v["aspect_ratio"],
                "duration": v["duration"],
                "description": v["description"]
            }
            for k, v in cls.TEMPLATES.items()
        ]

    @classmethod
    def hydrate_template(
        cls,
        template_id: str,
        variables: Optional[Dict[str, Any]] = None,
        brand: Optional[BrandKitSpec] = None,
        aspect_ratio: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Hydrates template with user variables and brand tokens,
        synthesizing an agency-grade MotionProjectIR.
        """
        if template_id not in cls.TEMPLATES:
            template_id = "flash_sale"

        tpl = cls.TEMPLATES[template_id]
        vars_merged = dict(tpl["default_vars"])
        if variables:
            vars_merged.update(variables)

        chosen_aspect = aspect_ratio or tpl["aspect_ratio"]
        if chosen_aspect == "9:16":
            w, h = 1080, 1920
        elif chosen_aspect == "1:1":
            w, h = 1080, 1080
        else:
            w, h = 1920, 1080

        # Colors from BrandKit or defaults
        p_primary = brand.colorPalette.primary if brand else "#D97706"
        p_dark = brand.colorPalette.backgroundDark if brand else "#090D16"
        p_card = brand.colorPalette.surfaceCardLight if brand else "#1E293B"
        font_headline = brand.typography.headingFont if brand else "Plus Jakarta Sans"

        scenes = [
            # 1. Visual Hook (0 - 2.2s)
            MotionScene(
                id="scene_1_hook",
                name="Hook",
                start=0.0,
                duration=2.2,
                backgroundColor=p_dark,
                layers=[
                    MotionLayer(
                        id="hook_title",
                        type="text",
                        start=0.1,
                        duration=2.1,
                        content={
                            "text": vars_merged.get("hook_title", "LOOK AT THIS"),
                            "fontSize": 64,
                            "color": "#FFFFFF",
                            "fontWeight": "800",
                            "fontFamily": font_headline,
                            "textAlign": "center"
                        },
                        animations=[
                            LayerAnimation(
                                property="scale",
                                from_value=0.8,
                                to_value=1.0,
                                start=0.0,
                                duration=0.4,
                                easing="power2.out"
                            ),
                            LayerAnimation(
                                property="opacity",
                                from_value=0.0,
                                to_value=1.0,
                                start=0.0,
                                duration=0.3
                            )
                        ]
                    ),
                    MotionLayer(
                        id="hook_sub",
                        type="text",
                        start=0.4,
                        duration=1.8,
                        content={
                            "text": vars_merged.get("hook_subtitle", ""),
                            "fontSize": 28,
                            "color": p_primary,
                            "fontWeight": "600"
                        },
                        animations=[
                            LayerAnimation(
                                property="y",
                                from_value=40.0,
                                to_value=0.0,
                                start=0.0,
                                duration=0.4
                            )
                        ]
                    )
                ]
            ),
            # 2. Agitation (2.2 - 6.0s)
            MotionScene(
                id="scene_2_agitation",
                name="Agitation",
                start=2.2,
                duration=3.8,
                backgroundColor=p_dark,
                layers=[
                    MotionLayer(
                        id="pain_headline",
                        type="text",
                        start=0.2,
                        duration=3.4,
                        content={
                            "text": vars_merged.get("problem", "The Common Problem"),
                            "fontSize": 38,
                            "color": "#E2E8F0"
                        },
                        animations=[
                            LayerAnimation(
                                property="opacity",
                                from_value=0.0,
                                to_value=1.0,
                                start=0.0,
                                duration=0.4
                            )
                        ]
                    )
                ]
            ),
            # 3. Aha! Climax (6.0 - 11.5s)
            MotionScene(
                id="scene_3_solution",
                name="Solution Climax",
                start=6.0,
                duration=5.5,
                backgroundColor=p_dark,
                layers=[
                    MotionLayer(
                        id="solution_hero",
                        type="text",
                        start=0.2,
                        duration=5.1,
                        content={
                            "text": vars_merged.get("solution", "The Pure Solution"),
                            "fontSize": 48,
                            "color": p_primary,
                            "fontWeight": "800"
                        },
                        animations=[
                            LayerAnimation(
                                property="scale",
                                from_value=0.75,
                                to_value=1.0,
                                start=0.0,
                                duration=0.5
                            )
                        ]
                    )
                ]
            ),
            # 4. Feature Blitz (11.5 - 15.5s)
            MotionScene(
                id="scene_4_blitz",
                name="Feature Blitz",
                start=11.5,
                duration=4.0,
                backgroundColor=p_dark,
                layers=[
                    MotionLayer(
                        id=f"feat_{idx}",
                        type="text",
                        start=0.3 + (idx * 0.8),
                        duration=3.5 - (idx * 0.8),
                        content={
                            "text": feat,
                            "fontSize": 24,
                            "color": "#FFFFFF",
                            "background": p_card
                        },
                        animations=[
                            LayerAnimation(
                                property="y",
                                from_value=30.0,
                                to_value=0.0,
                                start=0.0,
                                duration=0.3
                            )
                        ]
                    )
                    for idx, feat in enumerate(vars_merged.get("features", []))
                ]
            ),
            # 5. Frictionless CTA (15.5 - 18.0s)
            MotionScene(
                id="scene_5_cta",
                name="CTA",
                start=15.5,
                duration=2.5,
                backgroundColor=p_dark,
                layers=[
                    MotionLayer(
                        id="cta_pill",
                        type="text",
                        start=0.2,
                        duration=2.2,
                        content={
                            "text": vars_merged.get("cta_text", "SHOP NOW"),
                            "fontSize": 32,
                            "color": "#FFFFFF",
                            "background": p_primary,
                            "borderRadius": "30px",
                            "fontWeight": "bold"
                        },
                        animations=[
                            LayerAnimation(
                                property="scale",
                                from_value=0.85,
                                to_value=1.0,
                                start=0.0,
                                duration=0.4
                            )
                        ]
                    ),
                    MotionLayer(
                        id="cta_link",
                        type="text",
                        start=0.5,
                        duration=1.9,
                        content={
                            "text": vars_merged.get("cta_url", ""),
                            "fontSize": 20,
                            "color": "#94A3B8"
                        },
                        animations=[
                            LayerAnimation(
                                property="opacity",
                                from_value=0.0,
                                to_value=1.0,
                                start=0.0,
                                duration=0.3
                            )
                        ]
                    )
                ]
            )
        ]

        foley_cues = [
            FoleyCue(sound="sub_bass_drop", timestamp_sec=0.05, volume=0.85),
            FoleyCue(sound="cinematic_whoosh", timestamp_sec=2.2, volume=0.70),
            FoleyCue(sound="deep_riser", timestamp_sec=6.0, volume=0.75),
            FoleyCue(sound="camera_click", timestamp_sec=11.5, volume=0.60),
            FoleyCue(sound="notification_ding", timestamp_sec=15.5, volume=0.90),
        ]

        ir = MotionProjectIR(
            projectId=f"proj_{template_id}",
            title=tpl["name"],
            settings=ProjectSettings(
                width=w,
                height=h,
                fps=30,
                duration=tpl["duration"],
                aspectRatio=chosen_aspect,
                backgroundColor=p_dark
            ),
            scenes=scenes
        )
        res_dict = ir.model_dump()
        res_dict["foley_cues"] = [c.model_dump() for c in foley_cues]
        return res_dict
