import os
import json
from typing import Dict, Any, Optional, Type
from pydantic import BaseModel
from .base import BaseAIProvider, VideoKeyframeExtractor

class OpenAIProvider(BaseAIProvider):
    """
    OpenAI provider (GPT-4o, GPT-4o-mini, o3-mini) using the official `openai` SDK.
    Handles multimodal video by extracting sampled keyframes with timestamps.
    """
    def __init__(self, model_name: str = "gpt-4o", api_key: Optional[str] = None):
        super().__init__(model_name=model_name, api_key=api_key or os.getenv("OPENAI_API_KEY"))
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable.")
        
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError("The 'openai' package is required for OpenAIProvider. Run: uv pip install openai")

    def generate_structured_json(
        self,
        prompt: str,
        system_prompt: str,
        response_model: Optional[Type[BaseModel]] = None,
        temperature: float = 0.2
    ) -> Dict[str, Any]:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]

        if response_model is not None and issubclass(response_model, BaseModel):
            try:
                completion = self.client.beta.chat.completions.parse(
                    model=self.model_name,
                    messages=messages,
                    response_format=response_model,
                    temperature=temperature
                )
                return completion.choices[0].message.parsed.model_dump()
            except Exception:
                pass

        completion = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=temperature
        )
        return json.loads(completion.choices[0].message.content)

    def audit_video_saliency(
        self,
        video_path: str,
        prompt: str,
        response_model: Optional[Type[BaseModel]] = None
    ) -> Dict[str, Any]:
        # Extract 1 keyframe per second up to 24 frames
        extracted = VideoKeyframeExtractor.extract_keyframes_and_audio(video_path, fps=1.0, max_frames=24)
        
        content_items = [{"type": "text", "text": prompt + "\n\nAnalyze the following sequential video frames with timestamps:"}]
        for frame in extracted["frames"]:
            content_items.append({
                "type": "text",
                "text": f"[Timestamp: {frame['timestamp']}s]"
            })
            content_items.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{frame['base64']}",
                    "detail": "low"
                }
            })

        messages = [
            {"role": "system", "content": "You are an expert Performance Video Editor analyzing video frames for social media ads. Always return strictly valid JSON."},
            {"role": "user", "content": content_items}
        ]

        if response_model is not None and issubclass(response_model, BaseModel):
            try:
                completion = self.client.beta.chat.completions.parse(
                    model=self.model_name,
                    messages=messages,
                    response_format=response_model,
                    temperature=0.2
                )
                return completion.choices[0].message.parsed.model_dump()
            except Exception:
                pass

        completion = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.2
        )
        return json.loads(completion.choices[0].message.content)
