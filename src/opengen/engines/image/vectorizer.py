"""
Offline Raster-to-SVG Vectorizer Engine (Engine 3 Ecosystem Adapter).
Adapted from VTracer and visioncortex:
Converts raster bitmaps, silhouettes, and product contours into clean,
mathematical SVG paths (<svg><path d="..." /></svg>) locally without cloud APIs.
"""
import logging
from pathlib import Path
from typing import Union, Optional
from PIL import Image

logger = logging.getLogger(__name__)


class RasterVectorizer:
    """Converts raster images into vector SVG files."""

    @classmethod
    def vectorize_to_svg(
        cls,
        image_input: Union[str, Path, Image.Image],
        output_svg_path: Optional[Union[str, Path]] = None,
        color_hex: str = "#38bdf8",
        tolerance: float = 1.5
    ) -> str:
        """
        Traces contours from the input image and generates an SVG document.
        Returns the SVG string and optionally writes it to output_svg_path.
        """
        # Try vtracer if available
        try:
            import vtracer
            inp_path = str(image_input) if isinstance(image_input, (str, Path)) else None
            if inp_path and output_svg_path:
                vtracer.convert_image_to_svg_py(inp_path, str(output_svg_path))
                return Path(output_svg_path).read_text(encoding="utf-8")
        except ImportError:
            pass

        # Load image with PIL
        if isinstance(image_input, (str, Path)):
            pil_img = Image.open(str(image_input))
        elif isinstance(image_input, Image.Image):
            pil_img = image_input
        else:
            raise TypeError("Unsupported image input format.")

        width, height = pil_img.size

        # Trace contours with OpenCV
        try:
            import cv2
            import numpy as np

            # Convert to grayscale
            gray = np.array(pil_img.convert("L"))
            # Threshold to binary
            _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)

            # Find external contours
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            svg_paths = []
            for cnt in contours:
                if cv2.contourArea(cnt) < 10:
                    continue  # Ignore tiny noise

                # Smooth contour
                approx = cv2.approxPolyDP(cnt, epsilon=tolerance, closed=True)
                if len(approx) < 3:
                    continue

                # Build SVG path 'd' attribute
                d_cmds = []
                for idx, pt in enumerate(approx):
                    x, y = pt[0]
                    cmd = "M" if idx == 0 else "L"
                    d_cmds.append(f"{cmd}{x},{y}")
                d_cmds.append("Z")
                path_d = " ".join(d_cmds)
                svg_paths.append(f'<path d="{path_d}" fill="{color_hex}" fill-rule="evenodd" />')

            paths_markup = "\n  ".join(svg_paths)
            svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">
  {paths_markup}
</svg>"""

        except Exception as e:
            logger.warning(f"OpenCV vector contour tracing failed: {e}. Generating fallback SVG rect.")
            svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">
  <rect width="{width}" height="{height}" fill="{color_hex}" rx="12" />
</svg>"""

        if output_svg_path:
            out_p = Path(output_svg_path).resolve()
            out_p.parent.mkdir(parents=True, exist_ok=True)
            out_p.write_text(svg_content, encoding="utf-8")

        return svg_content
