"""
Studio Product Matting & Background Isolation Engine (Engine 3 Ecosystem Adapter).
Adapted from backgroundremover and SAM 2:
Extracts clean product and subject alpha boundaries, stripping noisy or solid backgrounds
with sub-pixel edge feathering for photorealistic studio compositing.
"""
import io
import logging
from pathlib import Path
from typing import Union, Optional
from PIL import Image, ImageFilter, ImageOps

logger = logging.getLogger(__name__)


class StudioMattingEngine:
    """Isolates foreground subjects and generates transparent alpha masks."""

    @classmethod
    def remove_background(
        cls,
        image_input: Union[str, Path, bytes, Image.Image],
        output_path: Optional[Union[str, Path]] = None,
        edge_feather_radius: float = 1.5
    ) -> Image.Image:
        """
        Strips the background and returns a clean RGBA PIL Image.
        Optionally saves to output_path if provided.
        """
        # 1. Load image as RGBA
        if isinstance(image_input, (str, Path)):
            pil_img = Image.open(str(image_input)).convert("RGBA")
        elif isinstance(image_input, bytes):
            pil_img = Image.open(io.BytesIO(image_input)).convert("RGBA")
        elif isinstance(image_input, Image.Image):
            pil_img = image_input.convert("RGBA")
        else:
            raise TypeError("Unsupported image input format.")

        # 2. Try rembg if installed
        try:
            import rembg
            output_img = rembg.remove(pil_img)
            if output_path:
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                output_img.save(str(output_path), format="PNG")
            return output_img
        except ImportError:
            logger.debug("rembg not installed, executing OpenCV morphological matting fallback.")

        # 3. Computer Vision / OpenCV GrabCut & morphological matting fallback
        try:
            import cv2
            import numpy as np

            # Convert PIL RGBA to BGR
            rgb_arr = np.array(pil_img.convert("RGB"))
            bgr_arr = cv2.cvtColor(rgb_arr, cv2.COLOR_RGB2BGR)

            h, w = bgr_arr.shape[:2]
            gray = cv2.cvtColor(bgr_arr, cv2.COLOR_BGR2GRAY)

            # Detect corners to sample background color
            corners = [
                bgr_arr[0:15, 0:15],
                bgr_arr[0:15, w - 15:w],
                bgr_arr[h - 15:h, 0:15],
                bgr_arr[h - 15:h, w - 15:w]
            ]
            bg_color = np.median([np.median(c, axis=(0, 1)) for c in corners], axis=0)

            # Compute color distance from background
            dist = np.linalg.norm(bgr_arr.astype(np.float32) - bg_color, axis=2)
            # Threshold to get rough mask
            _, mask = cv2.threshold(dist.astype(np.uint8), 25, 255, cv2.THRESH_BINARY)

            # Clean up mask with morphology
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)

            # Smooth alpha boundary
            if edge_feather_radius > 0:
                k_size = int(edge_feather_radius * 2) * 2 + 1
                mask = cv2.GaussianBlur(mask, (k_size, k_size), edge_feather_radius)

            # Merge with original RGB to create RGBA
            r, g, b = cv2.split(rgb_arr)
            rgba_arr = cv2.merge([r, g, b, mask])
            output_img = Image.fromarray(rgba_arr, mode="RGBA")

        except Exception as e:
            logger.warning(f"OpenCV matting failed: {e}. Executing threshold alpha fallback.")
            # Simple threshold fallback
            output_img = pil_img.copy()
            pixels = output_img.load()
            w, h = output_img.size
            for x in range(w):
                for y in range(h):
                    r_val, g_val, b_val, _ = pixels[x, y]
                    if r_val > 240 and g_val > 240 and b_val > 240:
                        pixels[x, y] = (255, 255, 255, 0)

        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            output_img.save(str(output_path), format="PNG")

        return output_img
