"""
Prompt-Hash Persistent Caching for Engine C.
Prevents duplicate API calls and credit expense on identical prompts while distinguishing
format and transparency parameters so unrelated options never collide.
"""
import hashlib
from typing import Optional
from opengen.cache.disk_store import cache_manager


class ImageCache:
    @staticmethod
    def compute_hash(
        prompt: str,
        aspect_ratio: str,
        style: str,
        provider: str,
        output_format: str = "png",
        transparent_background: bool = False,
    ) -> str:
        key = f"{prompt.strip().lower()}|{aspect_ratio}|{style}|{provider}|{output_format}|{transparent_background}"
        return hashlib.sha256(key.encode("utf-8")).hexdigest()

    @classmethod
    def get_cached_image(cls, prompt_hash: str) -> Optional[str]:
        return cache_manager.get_image_cache(prompt_hash)

    @classmethod
    def set_cached_image(cls, prompt_hash: str, file_path: str):
        cache_manager.set_image_cache(prompt_hash, file_path)
