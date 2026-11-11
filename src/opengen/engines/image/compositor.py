"""
Pillow Image Post-Processing Compositor.
Handles aspect ratio normalization, EXIF metadata stripping, and transparent PNG masking.
"""
import io
import logging
from PIL import Image, ImageOps

logger = logging.getLogger(__name__)

class ImageCompositor:
    """Post-processes raw generated image bytes."""

    @classmethod
    def process_image(
        cls,
        raw_bytes: bytes,
        mime_type: str,
        transparent_bg: bool = False
    ) -> bytes:
        if "svg" in mime_type:
            return raw_bytes

        img = Image.open(io.BytesIO(raw_bytes))

        # 1. Strip EXIF metadata
        data_no_exif = Image.new(img.mode, img.size)
        data_no_exif.putdata(list(img.getdata()))
        img = data_no_exif

        # 2. Transparent background alpha conversion if requested
        if transparent_bg:
            img = img.convert("RGBA")
            # Convert near-white background pixels to transparent
            datas = img.getdata()
            new_data = []
            for item in datas:
                # If pixel is close to pure white
                if item[0] > 240 and item[1] > 240 and item[2] > 240:
                    new_data.append((255, 255, 255, 0))
                else:
                    new_data.append(item)
            img.putdata(new_data)

        out_io = io.BytesIO()
        img.save(out_io, format="PNG", optimize=True)
        return out_io.getvalue()
