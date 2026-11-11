"""
Domain models for image generation (Engine C).
"""
from typing import Optional, Literal
from pydantic import BaseModel

class ImageRequest(BaseModel):
    prompt: str
    negative_prompt: Optional[str] = None
    aspect_ratio: str = "1:1"  # "1:1", "16:9", "9:16", "4:3", "3:4"
    output_format: str = "png"  # "png", "jpeg", "webp", "svg"
    style: str = "realistic"    # "realistic", "vector_illustration", "digital_art", "minimal"
    transparent_background: bool = False
    provider_preference: Optional[str] = None

class ImageResponse(BaseModel):
    file_path: str
    mime_type: str
    width: int
    height: int
    provider_used: str
    model_used: str
    cost_usd: float
    is_vector: bool = False
