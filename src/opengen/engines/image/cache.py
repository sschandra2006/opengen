"""
Prompt-Hash Persistent Caching for Engine C.
Prevents duplicate API calls and credit expense on identical prompts.
"""
import hashlib
from typing import Optional
from opengen.cache.disk_store import cache_manager

class ImageCache:
    @staticmethod
    def compute_hash(prompt: str, aspect_ratio: str, style: str, provider: str) -> str:
        key = f"{prompt.strip().lower()}|{aspect_ratio}|{style}|{provider}"
        return hashlib.sha256(key.encode("utf-8")).hexdigest()

    @classmethod
    def get_cached_image(cls, prompt_hash: str) -> Optional[str]:
        return cache_manager.get_image_cache(prompt_hash)

    @classmethod
    def set_cached_image(cls, prompt_hash: str, file_path: str):
        cache_manager.set_image_cache(prompt_hash, file_path)
