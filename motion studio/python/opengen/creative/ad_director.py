import os
from typing import Dict, Any, Optional
from pydantic import BaseModel
from opengen.ai.providers import AIProviderFactory, BaseAIProvider
from .footage_auditor import FootageAuditReport

class AdDirectorAgent:
    """
    Direct-Response Performance Ad Director for OpenGen Engine 5.
    Compiles creative briefs and video audit saliency into high-converting
    OpenGen IR v1.1.0 Projects strictly capped under 30 seconds.
    Works with ANY configured AI model (Gemini, OpenAI, Claude, Ollama, or Offline).
    """
    def __init__(
        self,
        provider: Optional[BaseAIProvider] = None,
        target_duration: float = 20.0,
        target_aspect: str = "9:16"
    ):
        self.provider = provider or AIProviderFactory.get_provider()
        self.target_duration = min(target_duration, 29.5)
        self.target_aspect = target_aspect

    def build_creative_ad_plan(
        self,
        brief: str,
        audit: Optional[FootageAuditReport] = None,
        rhythm_telemetry: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Synthesizes creative brief and video audit telemetry into an OpenGen IR v1.1.0 Project.
        """
        best_hook_desc = "Intriguing visual action"
        best_climax_desc = "Product reveal or payoff"
        clip_hook_start = 0.0
        clip_climax_start = 5.0

        if audit and audit.shots:
            best_hook = audit.top_hook_candidates[0] if audit.top_hook_candidates else audit.shots[0]
            best_climax = audit.top_climax_candidates[0] if audit.top_climax_candidates else audit.shots[-1]
            best_hook_desc = best_hook.action_summary
            best_climax_desc = best_climax.action_summary
            clip_hook_start = best_hook.start_time
            clip_climax_start = best_climax.start_time

        system_prompt = f"""
        You are the Master Performance Ad Director for OpenGen Engine 5.
        Given a creative brief and footage saliency, generate a complete, high-converting OpenGen IR v1.1.0 Project.
        
        Strict Requirements:
        1. Aspect ratio: "{self.target_aspect}" (1080x1920 for 9:16).
        2. Total duration must be strictly < 30.0s (target: {self.target_duration}s).
        3. Enforce the 5-Phase Conversion Funnel:
           - Phase 1 (0-2s): Hook (Punch-in 1.25x, foleyCue: "sub_impact_heavy", bold uppercase hook headline).
           - Phase 2 (2-6s): Agitation (Pain point text callout, animated badge, foleyCue: "whoosh_slide").
           - Phase 3 (6-12s): Climax (Product transformation, speedRamp leadIn=1.8 reveal=0.65, foleyCue: "riser_tension").
           - Phase 4 (12-15s): Feature Blitz (Fast micro-badges, 0.75s beat-synced cuts, foleyCue: "camera_click").
           - Phase 5 (15-18s): CTA (High-contrast pill button, clear action prompt, foleyCue: "notification_ding").
        4. Every scene must have `creativeAdDirectives` specifying funnelPhase, punchIn, audioPunctuation, and safeZoneEnforcement.
        5. Return strictly valid JSON adhering to OpenGen IR schemaVersion "1.1.0".
        """

        user_prompt = f"""
        Creative Brief: {brief}
        Identified Hook Clip: {best_hook_desc} (at {clip_hook_start}s)
        Identified Climax Clip: {best_climax_desc} (at {clip_climax_start}s)
        Target Duration: {self.target_duration}s
        Aspect Ratio: {self.target_aspect}
        """

        project_ir = self.provider.generate_structured_json(
            prompt=user_prompt,
            system_prompt=system_prompt,
            response_model=dict,
            temperature=0.3
        )

        return project_ir
