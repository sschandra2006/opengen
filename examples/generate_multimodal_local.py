"""
OpenGen Multi-Modal Generation Script (Running directly on your laptop).
Uses the uncensored Qwen 2.5 abliterated model (either running in local Ollama or on Kaggle)
to direct scripts, hooks, visual optics, and table structures.
Executes image generation, video ad composition, presentations, and documents right on your laptop!
"""
import os
from pathlib import Path
from opengen.client import OpenGenClient

# Initialize OpenGen client locally on your laptop
client = OpenGenClient()

print("=" * 70)
print("[OpenGen Multi-Modal Studio - Running Locally On Laptop]")
print("=" * 70)

# -----------------------------------------------------------------------------
# 1. Video Ad Generation (Motion Graphics Studio)
# -----------------------------------------------------------------------------
print("\n[1/3] Generating Video Ad...")
video_result = client.motion.generate_ad(
    brief="Underground cyberpunk synthwave music release. High energy, neon typography, heavy bass drops.",
    target_duration=15.0,
    target_aspect="9:16"
)
print(f"-> Video Ad created: {video_result.mp4_path}")


# -----------------------------------------------------------------------------
# 2. Studio Image Generation (Image Studio)
# -----------------------------------------------------------------------------
print("\n[2/3] Generating Studio Product Image...")
image_result = client.images.generate(
    prompt="A luxury frosted glass perfume bottle on raw black slate, surrounded by gentle water mist and soft rim lighting",
    aspect_ratio="1:1",
    style="photorealistic",
    apply_optical_physics=True
)
print(f"-> Image created: {image_result.file_path}")


# -----------------------------------------------------------------------------
# 3. Presentation Deck (Presentation Studio)
# -----------------------------------------------------------------------------
print("\n[3/3] Generating 12-Column Bento Presentation Deck...")
deck_result = client.presentations.generate(
    topic="Next-Gen Autonomous Multi-Modal Content Generation",
    slide_count=5,
    theme="executive_dark"
)
print(f"-> PowerPoint Presentation created: {deck_result.file_path}")

print("\n" + "=" * 70)
print("All multi-modal outputs generated successfully inside output/ directory!")
print("=" * 70)
