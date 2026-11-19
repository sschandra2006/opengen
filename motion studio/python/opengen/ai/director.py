import os
import json
from typing import Dict, Any, Optional
from opengen.ai.providers import AIProviderFactory, BaseAIProvider

STORYBOARD_SYSTEM_PROMPT = """
You are the Motion Graphics Director for OpenGen Engine 5.
Given a user creative brief, produce a valid, parseable JSON Project matching the OpenGen IR schema.
Structure the video into concise, 2-4 second dynamic scenes.
Choose expressive kinetic typography, color palettes, and GSAP easings.
Return ONLY valid JSON.
"""

class Director:
    """
    OpenGen Studio Storyboard & Scene Director.
    Powered by the model-agnostic AIProviderFactory.
    """
    def __init__(self, provider: Optional[BaseAIProvider] = None, provider_name: Optional[str] = None):
        self.provider = provider or AIProviderFactory.get_provider(provider_name=provider_name)

    def create_storyboard(
        self,
        prompt: str,
        duration_sec: float = 15.0,
        aspect_ratio: str = "9:16",
        style: str = "tech"
    ) -> Dict[str, Any]:
        """
        Generate complete OpenGen IR Project JSON from natural language brief.
        Dispatches via the configured AI provider with automatic offline fallback.
        """
        req_prompt = f"""Creative Brief: {prompt}
Target Duration: {duration_sec} seconds
Aspect Ratio: {aspect_ratio}
Visual Style: {style}

Generate the complete OpenGen Project IR JSON according to schema."""

        try:
            return self.provider.generate_structured_json(
                prompt=req_prompt,
                system_prompt=STORYBOARD_SYSTEM_PROMPT,
                response_model=dict,
                temperature=0.3
            )
        except Exception as e:
            print(f"[Director] Primary provider failed: {e}. Switching to offline fallback.")
            from opengen.ai.providers.offline_provider import OfflineDeterministicProvider
            fallback = OfflineDeterministicProvider()
            return fallback.generate_structured_json(prompt, STORYBOARD_SYSTEM_PROMPT)
