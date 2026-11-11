"""
OpenAI DALL-E 3 Adapter.
"""
import base64
import logging
from typing import Tuple
import httpx
from opengen.config import settings
from opengen.domain.image import ImageRequest
from opengen.engines.image.providers.base import AbstractImageProvider
from opengen.domain.errors import ProviderError

logger = logging.getLogger(__name__)

DALLE_SIZE_MAP = {
    "1:1": "1024x1024",
    "16:9": "1792x1024",
    "9:16": "1024x1792"
}

class OpenAIDalleAdapter(AbstractImageProvider):
    """Adapter for OpenAI DALL-E 3."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.endpoint = "https://api.openai.com/v1/images/generations"

    def generate(self, request: ImageRequest) -> Tuple[bytes, str, float]:
        if not self.api_key:
            raise ProviderError("Missing OPENAI_API_KEY for DALL-E 3 image generation.")

        size = DALLE_SIZE_MAP.get(request.aspect_ratio, "1024x1024")
        payload = {
            "model": "dall-e-3",
            "prompt": request.prompt,
            "size": size,
            "quality": "standard",
            "response_format": "b64_json"
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            with httpx.Client(timeout=60.0) as client:
                res = client.post(self.endpoint, json=payload, headers=headers)
                res.raise_for_status()
                data = res.json()
                b64_data = data["data"][0]["b64_json"]
                img_bytes = base64.b64decode(b64_data)
                return img_bytes, "image/png", 0.040
        except Exception as e:
            logger.error(f"OpenAI DALL-E 3 generation failed: {e}")
            raise ProviderError(f"DALL-E 3 generation failed: {e}") from e
