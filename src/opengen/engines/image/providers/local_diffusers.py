"""
Local GPU Image Generation Adapter using HuggingFace Diffusers.
Enables 100% free, offline, uncensored photorealistic image generation on GPU (e.g. Kaggle Tesla T4 16GB).
Supports models like stabilityai/sdxl-turbo, stabilityai/sd-turbo, or any local uncensored checkpoint.
"""
import io
import logging
from typing import Tuple, Optional
from opengen.config import settings
from opengen.domain.image import ImageRequest
from opengen.engines.image.providers.base import AbstractImageProvider
from opengen.domain.errors import ProviderError

logger = logging.getLogger(__name__)

DIMENSION_MAP = {
    "1:1": (512, 512),
    "16:9": (768, 432),
    "9:16": (432, 768),
    "4:3": (640, 480),
    "3:4": (480, 640)
}


class LocalDiffusersAdapter(AbstractImageProvider):
    """Adapter for running local Hugging Face diffusion models on GPU."""

    def __init__(self, model_id: str = "stabilityai/sd-turbo"):
        self.model_id = model_id
        self._pipe = None

    def _load_pipeline(self):
        if self._pipe is None:
            try:
                import torch
                from diffusers import AutoPipelineForText2Image
                device = "cuda" if torch.cuda.is_available() else "cpu"
                dtype = torch.float16 if device == "cuda" else torch.float32

                logger.info(f"Loading local diffusion pipeline '{self.model_id}' on {device} ({dtype})...")
                self._pipe = AutoPipelineForText2Image.from_pretrained(
                    self.model_id,
                    torch_dtype=dtype,
                    variant="fp16" if device == "cuda" else None
                )
                self._pipe.to(device)
                if device == "cuda":
                    # Enable memory-efficient attention if available
                    try:
                        self._pipe.enable_attention_slicing()
                    except Exception:
                        pass
                logger.info("Local diffusion pipeline loaded successfully.")
            except Exception as e:
                raise ProviderError(f"Failed to load local diffusers pipeline: {e}")
        return self._pipe

    def is_available(self) -> bool:
        """Checks if torch and diffusers can be imported."""
        try:
            import torch
            import diffusers
            return True
        except ImportError:
            return False

    def generate(self, request: ImageRequest) -> Tuple[bytes, str, float]:
        pipe = self._load_pipeline()
        w, h = DIMENSION_MAP.get(request.aspect_ratio, (512, 512))

        logger.info(f"Generating local image with prompt: {request.prompt[:80]}... ({w}x{h})")
        # For turbo models, 1-4 steps is optimal; for standard, 20-30 steps
        num_steps = 1 if "turbo" in self.model_id.lower() else 20
        guidance = 0.0 if "turbo" in self.model_id.lower() else 7.5

        generator_kwargs = {
            "prompt": request.prompt,
            "width": w,
            "height": h,
            "num_inference_steps": num_steps,
            "guidance_scale": guidance,
        }
        if request.negative_prompt and guidance > 1.0:
            generator_kwargs["negative_prompt"] = request.negative_prompt

        output = pipe(**generator_kwargs)
        image = output.images[0]

        buf = io.BytesIO()
        image.save(buf, format="PNG")
        raw_bytes = buf.getvalue()

        return raw_bytes, "image/png", 0.0  # 0.0 USD cost on local GPU
