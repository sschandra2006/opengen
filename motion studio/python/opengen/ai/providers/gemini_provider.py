import os
import json
import time
from typing import Dict, Any, Optional, Type
from pydantic import BaseModel
from .base import BaseAIProvider

class GeminiProvider(BaseAIProvider):
    """
    Google Gemini provider leveraging the modern `google-genai` SDK.
    Supports native video file upload via the Gemini Files API.
    """
    def __init__(self, model_name: str = "gemini-2.0-flash", api_key: Optional[str] = None):
        super().__init__(model_name=model_name, api_key=api_key or os.getenv("GEMINI_API_KEY"))
        if not self.api_key:
            raise ValueError("Gemini API key is required. Set GEMINI_API_KEY environment variable.")
        
        try:
            from google import genai
            self.client = genai.Client(api_key=self.api_key)
        except ImportError:
            raise ImportError("The 'google-genai' package is required for GeminiProvider. Run: uv pip install google-genai")

    def generate_structured_json(
        self,
        prompt: str,
        system_prompt: str,
        response_model: Optional[Type[BaseModel]] = None,
        temperature: float = 0.2
    ) -> Dict[str, Any]:
        from google.genai import types

        config_args: Dict[str, Any] = {
            "system_instruction": system_prompt,
            "response_mime_type": "application/json",
            "temperature": temperature
        }
        if response_model is not None and issubclass(response_model, BaseModel):
            config_args["response_schema"] = response_model

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(**config_args)
        )
        return json.loads(response.text)

    def audit_video_saliency(
        self,
        video_path: str,
        prompt: str,
        response_model: Optional[Type[BaseModel]] = None
    ) -> Dict[str, Any]:
        from google.genai import types

        # Upload video to Gemini Files API
        video_file = self.client.files.upload(file=video_path)
        
        # Poll file state until ACTIVE if large
        while video_file.state.name == "PROCESSING":
            time.sleep(1)
            video_file = self.client.files.get(name=video_file.name)

        config_args: Dict[str, Any] = {
            "response_mime_type": "application/json",
            "temperature": 0.2
        }
        if response_model is not None and issubclass(response_model, BaseModel):
            config_args["response_schema"] = response_model

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=[video_file, prompt],
            config=types.GenerateContentConfig(**config_args)
        )

        # Cleanup file after analysis
        try:
            self.client.files.delete(name=video_file.name)
        except Exception:
            pass

        return json.loads(response.text)
