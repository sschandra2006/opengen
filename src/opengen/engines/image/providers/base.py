"""
Base interface for image generation provider adapters.
"""
from abc import ABC, abstractmethod
from typing import Tuple
from opengen.domain.image import ImageRequest

class AbstractImageProvider(ABC):
    """Abstract interface implemented by all image generation provider adapters."""

    @abstractmethod
    def generate(self, request: ImageRequest) -> Tuple[bytes, str, float]:
        """
        Executes generation call.
        Returns: (image_bytes, mime_type, cost_usd)
        """
        pass
