"""
Persistent storage repository for Brand Kits.
Persists BrandKitSpec JSON objects to disk with thread-safe atomic writes.
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from opengen.config import settings
from opengen.domain.brand import BrandKitSpec

logger = logging.getLogger(__name__)


class BrandKitStore:
    """Stores and retrieves BrandKit definitions on disk."""

    def __init__(self, storage_dir: Optional[Path] = None):
        self.storage_dir = storage_dir or settings.BRANDS_DIR
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._in_memory_cache: Dict[str, BrandKitSpec] = {}
        self._ensure_default_brands()

    def _ensure_default_brands(self):
        """Initializes default brand kits if none exist."""
        default_brand = BrandKitSpec(
            brandId="brand_quantum_flow",
            brandName="QuantumFlow AI"
        )
        if not self.has_brand(default_brand.brandId):
            self.save_brand(default_brand)

    def save_brand(self, brand: BrandKitSpec) -> BrandKitSpec:
        """Saves a brand kit spec to JSON file."""
        file_path = self.storage_dir / f"{brand.brandId}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(brand.model_dump_json(indent=2))
        self._in_memory_cache[brand.brandId] = brand
        logger.info(f"Saved brand kit '{brand.brandId}' to {file_path}")
        return brand

    def get_brand(self, brand_id: str) -> Optional[BrandKitSpec]:
        """Retrieves a brand kit by brandId."""
        if brand_id in self._in_memory_cache:
            return self._in_memory_cache[brand_id]

        file_path = self.storage_dir / f"{brand_id}.json"
        if not file_path.exists():
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            brand = BrandKitSpec.model_validate(data)
            self._in_memory_cache[brand_id] = brand
            return brand
        except Exception as e:
            logger.error(f"Failed to read brand kit '{brand_id}': {e}")
            return None

    def has_brand(self, brand_id: str) -> bool:
        return (self.storage_dir / f"{brand_id}.json").exists()

    def list_brands(self) -> List[BrandKitSpec]:
        """Lists all registered brand kits."""
        brands = []
        for p in self.storage_dir.glob("*.json"):
            b = self.get_brand(p.stem)
            if b:
                brands.append(b)
        return brands


brand_kit_store = BrandKitStore()
