"""
OpenGen Laptop Remote Client.
Connects your local laptop directly to the Kaggle GPU backend running OpenGen via Cloudflare Tunnel.
Allows generating uncensored videos, images, presentations, and documents from your laptop terminal or scripts.
"""
import os
import sys
import time
import requests
from pathlib import Path
from typing import Optional, Dict, Any


class RemoteOpenGen:
    """Remote bridge connecting your laptop to the Kaggle GPU server."""

    def __init__(self, backend_url: str):
        self.base_url = backend_url.rstrip("/")
        self.api_v1 = f"{self.base_url}/api/v1"
        self._verify_connection()

    def _verify_connection(self):
        try:
            resp = requests.get(f"{self.api_v1}/health", timeout=10)
            if resp.status_code == 200:
                print(f"[RemoteOpenGen] Connected to remote GPU backend: {self.base_url}")
            else:
                print(f"[RemoteOpenGen] Warning: Backend responded with status {resp.status_code}")
        except Exception as e:
            print(f"[RemoteOpenGen] Error connecting to {self.base_url}: {e}")

    def generate_video(
        self,
        brief: str,
        duration: float = 15.0,
        aspect_ratio: str = "9:16",
        save_to: str = "downloaded_ad.mp4"
    ) -> str:
        """
        Dispatches a video generation job to the remote GPU backend.
        Kaggle uses the uncensored model for ad directing and renders the video via FFmpeg.
        """
        print(f"\n[Video Generation] Requesting video: '{brief[:60]}...' ({aspect_ratio}, {duration}s)")
        payload = {
            "brief": brief,
            "target_duration": duration,
            "target_aspect": aspect_ratio
        }

        resp = requests.post(f"{self.api_v1}/motion/ad", json=payload, timeout=300)
        resp.raise_for_status()
        data = resp.json()

        job_id = data.get("job_id")
        mp4_remote_path = data.get("mp4_path", "")
        print(f"[Video Generation] Job completed on GPU: {job_id}")

        # Download the rendered video back to laptop
        filename = Path(mp4_remote_path).name if mp4_remote_path else "rendered_ad.mp4"
        download_url = f"{self.api_v1}/artifacts/{job_id}/{filename}/dl"
        
        dl_resp = requests.get(download_url, stream=True)
        out_path = Path(save_to)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "wb") as f:
            for chunk in dl_resp.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"[Video Generation] Video downloaded to your laptop: {out_path.resolve()}")
        return str(out_path.resolve())

    def generate_image(
        self,
        prompt: str,
        aspect_ratio: str = "1:1",
        style: str = "photorealistic",
        save_to: str = "downloaded_image.png"
    ) -> str:
        """
        Generates an uncensored photorealistic image on the remote GPU and downloads it locally.
        """
        print(f"\n[Image Generation] Generating image: '{prompt[:60]}...' ({aspect_ratio})")
        payload = {
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "style": style,
            "provider_preference": "local",
            "apply_optical_physics": True
        }

        resp = requests.post(f"{self.api_v1}/images/generate", json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()

        job_id = data.get("job_id")
        img_remote_path = data.get("file_path", "")
        filename = Path(img_remote_path).name if img_remote_path else "generated_image.png"

        download_url = f"{self.api_v1}/artifacts/{job_id}/{filename}/dl"
        dl_resp = requests.get(download_url, stream=True)

        out_path = Path(save_to)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "wb") as f:
            for chunk in dl_resp.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"[Image Generation] Image downloaded to your laptop: {out_path.resolve()}")
        return str(out_path.resolve())

    def generate_document(
        self,
        title: str,
        executive_summary: str,
        findings: list = None,
        save_to: str = "downloaded_report.pdf"
    ) -> str:
        """
        Compiles a Swiss Editorial Typst document on Kaggle and downloads the vector PDF locally.
        """
        print(f"\n[Document Generation] Compiling publication document: '{title}'")
        payload = {
            "title": title,
            "executive_summary": executive_summary,
            "findings": findings or ["System operational", "Token reduction verified"]
        }

        resp = requests.post(f"{self.api_v1}/documents/typst", json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()

        pdf_remote_path = data.get("pdf_path", "")
        job_id = data.get("job_id")
        filename = Path(pdf_remote_path).name if pdf_remote_path else "document.pdf"

        download_url = f"{self.api_v1}/artifacts/{job_id}/{filename}/dl"
        dl_resp = requests.get(download_url, stream=True)

        out_path = Path(save_to)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "wb") as f:
            for chunk in dl_resp.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"[Document Generation] PDF downloaded to your laptop: {out_path.resolve()}")
        return str(out_path.resolve())


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/laptop_remote_client.py <CLOUDFLARE_TUNNEL_URL>")
        print("Example: python scripts/laptop_remote_client.py https://my-subdomain.trycloudflare.com")
        sys.exit(1)

    tunnel_url = sys.argv[1]
    client = RemoteOpenGen(tunnel_url)

    # Example 1: Generate an uncensored video ad
    client.generate_video(
        brief="Commercial ad for an underground cyberpunk synthwave vinyl release. High energy, neon typography.",
        save_to="laptop_downloads/cyberpunk_ad.mp4"
    )

    # Example 2: Generate an uncensored studio image
    client.generate_image(
        prompt="Studio photography of a sleek titanium mechanical watch on wet granite stone, dramatic macro rim lighting",
        save_to="laptop_downloads/watch_photo.png"
    )
