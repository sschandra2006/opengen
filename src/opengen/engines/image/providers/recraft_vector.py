"""
Recraft AI Vector V4 Adapter.
Generates true, scalable, multi-layer SVG vector assets.
"""
import logging
from typing import Tuple
import httpx
from opengen.config import settings
from opengen.domain.image import ImageRequest
from opengen.engines.image.providers.base import AbstractImageProvider
from opengen.domain.errors import ProviderError

logger = logging.getLogger(__name__)

class RecraftVectorAdapter(AbstractImageProvider):
    """Adapter for Recraft AI Vector V4 API generating clean SVGs."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.RECRAFT_API_KEY
        self.endpoint = "https://external.api.recraft.ai/v1/images/generations"

    def generate(self, request: ImageRequest) -> Tuple[bytes, str, float]:
        if not self.api_key:
            # Fallback mock SVG for development testing if no paid Recraft key is configured
            mock_svg = (
                f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 500">'
                f'<rect width="500" height="500" rx="40" fill="#2563EB"/>'
                f'<text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" '
                f'fill="#FFFFFF" font-size="24" font-family="sans-serif">{request.prompt[:30]}</text>'
                f'</svg>'
            ).encode("utf-8")
            return mock_svg, "image/svg+xml", 0.0

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "prompt": request.prompt,
            "style": "vector_illustration",
            "model": "recraft-v4-vector",
            "format": "svg"
        }

        try:
            with httpx.Client(timeout=60.0) as client:
                res = client.post(self.endpoint, json=payload, headers=headers)
                res.raise_for_status()
                data = res.json()
                svg_url = data["data"][0]["url"]
                svg_res = client.get(svg_url)
                return svg_res.content, "image/svg+xml", 0.040
        except Exception as e:
            logger.error(f"Recraft Vector generation failed: {e}")
            raise ProviderError(f"Recraft generation failed: {e}") from e
