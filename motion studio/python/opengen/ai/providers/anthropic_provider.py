import os
import json
import re
from typing import Dict, Any, Optional, Type
from pydantic import BaseModel
from .base import BaseAIProvider, VideoKeyframeExtractor

class AnthropicProvider(BaseAIProvider):
    """
    Anthropic Claude provider (Claude 3.7 Sonnet, Claude 3.5 Haiku) using `anthropic` SDK.
    Handles multimodal video through sequential image content blocks.
    """
    def __init__(self, model_name: str = "claude-3-7-sonnet-20250219", api_key: Optional[str] = None):
        super().__init__(model_name=model_name, api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))
        if not self.api_key:
            raise ValueError("Anthropic API key is required. Set ANTHROPIC_API_KEY environment variable.")

        try:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=self.api_key)
        except ImportError:
            raise ImportError("The 'anthropic' package is required for AnthropicProvider. Run: uv pip install anthropic")

    def generate_structured_json(
        self,
        prompt: str,
        system_prompt: str,
        response_model: Optional[Type[BaseModel]] = None,
        temperature: float = 0.2
    ) -> Dict[str, Any]:
        full_system = system_prompt + "\nYou must return strictly valid JSON. Do not wrap in markdown quotes if possible, or use standard ```json blocks."
        
        message = self.client.messages.create(
            model=self.model_name,
            max_tokens=4096,
            temperature=temperature,
            system=full_system,
            messages=[{"role": "user", "content": prompt}]
        )

        text = message.content[0].text.strip()
        return self._extract_json(text)

    def audit_video_saliency(
        self,
        video_path: str,
        prompt: str,
        response_model: Optional[Type[BaseModel]] = None
    ) -> Dict[str, Any]:
        extracted = VideoKeyframeExtractor.extract_keyframes_and_audio(video_path, fps=1.0, max_frames=20)

        content_items = [{"type": "text", "text": prompt + "\n\nAnalyze the following sequential video frames with timestamps. Return valid JSON only."}]
        for frame in extracted["frames"]:
            content_items.append({
                "type": "text",
                "text": f"Timestamp: {frame['timestamp']}s"
            })
            content_items.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": frame["base64"]
                }
            })

        message = self.client.messages.create(
            model=self.model_name,
            max_tokens=4096,
            temperature=0.2,
            messages=[{"role": "user", "content": content_items}]
        )

        text = message.content[0].text.strip()
        return self._extract_json(text)

    def _extract_json(self, text: str) -> Dict[str, Any]:
        try:
            return json.loads(text)
        except Exception:
            # Match ```json ... ```
            match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
            if match:
                return json.loads(match.group(1))
            # Find first { and last }
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1:
                return json.loads(text[start:end+1])
            raise ValueError(f"Failed to parse valid JSON from Claude output: {text[:200]}...")
