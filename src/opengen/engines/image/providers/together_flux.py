"""
Together AI FLUX.1 [schnell] Adapter (Apache 2.0 open weights).
Fast 4-step generation with photorealistic anatomy and accurate text spelling.
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

# Map aspect ratios to exact pixel dimensions divisible by 16
DIMENSION_MAP = {
    "1:1": (1024, 1024),
    "16:9": (1344, 768),
    "9:16": (768, 1344),
    "4:3": (1152, 864),
    "3:4": (864, 1152)
}

class TogetherFluxAdapter(AbstractImageProvider):
    """Adapter for Together AI BFL FLUX.1 [schnell] API."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.TOGETHER_API_KEY
        self.endpoint = "https://api.together.xyz/v1/images/generations"

    def generate(self, request: ImageRequest) -> Tuple[bytes, str, float]:
        if not self.api_key:
            raise ProviderError("Missing TOGETHER_API_KEY for FLUX.1 image generation.")

        w, h = DIMENSION_MAP.get(request.aspect_ratio, (1024, 1024))
        payload = {
            "model": "black-forest-labs/FLUX.1-schnell",
            "prompt": request.prompt,
            "width": w,
            "height": h,
            "steps": 4,
            "n": 1,
            "response_format": "b64_json"
        }
        if request.negative_prompt:
            payload["negative_prompt"] = request.negative_prompt

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
                return img_bytes, "image/png", 0.035
        except Exception as e:
            logger.error(f"Together FLUX.1 generation failed: {e}")
            raise ProviderError(f"FLUX.1 generation failed: {e}") from e
