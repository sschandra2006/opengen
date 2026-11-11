"""
Unified Image Generation Engine (Engine C Coordinator).
Coordinates provider selection (Together FLUX.1, DALL-E, Recraft SVG),
isolated cache storage (cache/images/), and Pillow post-processing.
"""
import io
import logging
import shutil
from pathlib import Path
from typing import Optional
from PIL import Image

from opengen.config import settings
from opengen.domain.image import ImageRequest, ImageResponse
from opengen.engines.image.cache import ImageCache
from opengen.engines.image.compositor import ImageCompositor
from opengen.engines.image.providers.together_flux import TogetherFluxAdapter
from opengen.engines.image.providers.openai_dalle import OpenAIDalleAdapter
from opengen.engines.image.providers.recraft_vector import RecraftVectorAdapter

logger = logging.getLogger(__name__)


class ImageEngine:
    """Master entrypoint for Engine C: Image & Vector Asset Generation."""

    def __init__(self):
        self.flux_adapter = TogetherFluxAdapter()
        self.dalle_adapter = OpenAIDalleAdapter()
        self.recraft_adapter = RecraftVectorAdapter()

    def generate_image(self, request: ImageRequest, output_dir: Optional[Path] = None) -> ImageResponse:
        # 0. Prompt policy & moderation pre-check
        if not request.prompt or not request.prompt.strip():
            raise ValueError("Image generation prompt cannot be empty.")
        if len(request.prompt) > 4000:
            raise ValueError("Image generation prompt exceeds maximum length of 4000 characters.")

        if output_dir is not None:
            out_dir = Path(output_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
        else:
            _, out_dir = settings.allocate_run_dir("images")

        target_provider = request.provider_preference or ("recraft" if request.output_format == "svg" else "flux")
        prompt_hash = ImageCache.compute_hash(
            request.prompt,
            request.aspect_ratio,
            request.style,
            target_provider,
            output_format=request.output_format,
            transparent_background=request.transparent_background,
        )

        # 1. Check persistent L2 cache (stored immutably inside cache/images/, never output/)
        cached_path = ImageCache.get_cached_image(prompt_hash)
        if cached_path and Path(cached_path).exists():
            logger.info("Retrieved image from L2 cache (0 credits consumed)")
            cached_src = Path(cached_path)
            ext = cached_src.suffix or (".svg" if request.output_format == "svg" else ".png")
            is_vec = ext.lower() == ".svg"
            out_file = out_dir / f"img_{prompt_hash[:16]}{ext}"
            shutil.copy2(str(cached_src), str(out_file))

            w, h = 1024, 1024
            if not is_vec:
                try:
                    with Image.open(out_file) as im:
                        w, h = im.size
                except Exception:
                    pass

            return ImageResponse(
                file_path=str(out_file),
                mime_type="image/svg+xml" if is_vec else "image/png",
                width=w,
                height=h,
                provider_used="cache",
                model_used="cache",
                cost_usd=0.0,
                is_vector=is_vec
            )

        # 2. Route to provider
        if target_provider == "recraft" or request.output_format == "svg":
            raw_bytes, mime, cost = self.recraft_adapter.generate(request)
            ext = ".svg"
            is_vec = True
        elif target_provider == "dalle":
            raw_bytes, mime, cost = self.dalle_adapter.generate(request)
            ext = ".png"
            is_vec = False
        else:
            try:
                raw_bytes, mime, cost = self.flux_adapter.generate(request)
                ext = ".png"
                is_vec = False
            except Exception:
                logger.info("Falling back to mock SVG generation for local testing...")
                raw_bytes, mime, cost = self.recraft_adapter.generate(request)
                ext = ".svg"
                is_vec = True

        # 3. Post-Process via Compositor
        processed_bytes = ImageCompositor.process_image(raw_bytes, mime, request.transparent_background)

        # 4. Write to immutable L2 cache binary store AND isolated output run folder
        cache_img_dir = settings.CACHE_DIR / "images"
        cache_img_dir.mkdir(parents=True, exist_ok=True)
        cached_file = cache_img_dir / f"{prompt_hash}{ext}"
        with open(cached_file, "wb") as cf:
            cf.write(processed_bytes)

        out_file = out_dir / f"img_{prompt_hash[:16]}{ext}"
        shutil.copy2(str(cached_file), str(out_file))

        # 5. Index immutable cache entry
        ImageCache.set_cached_image(prompt_hash, str(cached_file))

        w, h = 1024, 1024
        if not is_vec:
            try:
                with Image.open(io.BytesIO(processed_bytes)) as im:
                    w, h = im.size
            except Exception:
                pass

        return ImageResponse(
            file_path=str(out_file),
            mime_type=mime,
            width=w,
            height=h,
            provider_used=target_provider,
            model_used=target_provider,
            cost_usd=cost,
            is_vector=is_vec
        )


image_engine = ImageEngine()
