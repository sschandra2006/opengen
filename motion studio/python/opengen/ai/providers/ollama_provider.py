import os
import json
import re
import requests
from typing import Dict, Any, Optional, Type
from pydantic import BaseModel
from .base import BaseAIProvider, VideoKeyframeExtractor

class OllamaProvider(BaseAIProvider):
    """
    Local Open-Weights Provider for Ollama, vLLM, LMStudio, and LocalAI.
    Offers completely private, offline, zero-cloud API dependency.
    Supports DeepSeek-R1, Qwen2.5, Llama-3.3, and Qwen2-VL.
    """
    def __init__(
        self,
        base_url: str = "http://127.0.0.1:11434/v1",
        model_name: str = "qwen2.5:14b",
        vision_model: str = "qwen2-vl"
    ):
        super().__init__(model_name=model_name)
        self.base_url = base_url.rstrip("/")
        self.vision_model = vision_model

    def generate_structured_json(
        self,
        prompt: str,
        system_prompt: str,
        response_model: Optional[Type[BaseModel]] = None,
        temperature: float = 0.2
    ) -> Dict[str, Any]:
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt + "\nReturn ONLY valid JSON. No conversational preamble."},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "response_format": {"type": "json_object"}
        }

        try:
            res = requests.post(url, json=payload, timeout=60)
            res.raise_for_status()
            data = res.json()
            content = data["choices"][0]["message"]["content"]
            return self._extract_json(content)
        except Exception as e:
            raise RuntimeError(f"Ollama/vLLM request failed at {url}: {e}")

    def audit_video_saliency(
        self,
        video_path: str,
        prompt: str,
        response_model: Optional[Type[BaseModel]] = None
    ) -> Dict[str, Any]:
        url = f"{self.base_url}/chat/completions"
        extracted = VideoKeyframeExtractor.extract_keyframes_and_audio(video_path, fps=0.5, max_frames=12)

        content_items = [{"type": "text", "text": prompt + "\nAnalyze these video frames for viral ad metrics. Output JSON only."}]
        for frame in extracted["frames"]:
            content_items.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{frame['base64']}"
                }
            })

        payload = {
            "model": self.vision_model or self.model_name,
            "messages": [
                {"role": "system", "content": "You are a performance video analysis AI. Return strictly valid JSON."},
                {"role": "user", "content": content_items}
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"}
        }

        try:
            res = requests.post(url, json=payload, timeout=120)
            res.raise_for_status()
            content = res.json()["choices"][0]["message"]["content"]
            return self._extract_json(content)
        except Exception as e:
            raise RuntimeError(f"Ollama vision analysis failed: {e}")

    def _extract_json(self, text: str) -> Dict[str, Any]:
        try:
            return json.loads(text)
        except Exception:
            match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
            if match:
                return json.loads(match.group(1))
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1:
                return json.loads(text[start:end+1])
            raise ValueError(f"Failed to extract JSON from local LLM response: {text[:200]}")
