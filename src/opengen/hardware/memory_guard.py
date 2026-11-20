"""
Memory Guard and OOM Circuit Breaker for OpenGen.
Provides an execution context manager that proactively monitors memory pressure,
intercepts out-of-memory errors, evicts cached buffers, and triggers graceful fallbacks.
"""
import gc
import logging
from typing import Optional
import psutil

logger = logging.getLogger(__name__)


class HardwareMemoryError(Exception):
    """Raised when available memory or GPU VRAM is insufficient to complete the task."""
    pass


class MemoryGuard:
    """Execution context manager providing real-time memory monitoring and OOM interception."""

    def __init__(
        self,
        max_ram_pct: float = 88.0,
        auto_evict: bool = True,
        operation_name: str = "generative_task"
    ):
        self.max_ram_pct = max_ram_pct
        self.auto_evict = auto_evict
        self.operation_name = operation_name

    def __enter__(self):
        self._pre_check()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            # Check for memory errors (standard MemoryError or PyTorch CUDA OOM)
            is_oom = (
                issubclass(exc_type, MemoryError) or
                "out of memory" in str(exc_val).lower() or
                "cuda out of memory" in str(exc_val).lower()
            )
            if is_oom:
                logger.error(f"MemoryGuard caught OOM during '{self.operation_name}': {exc_val}. Evicting cache...")
                self.evict_memory()
                # Wrap in HardwareMemoryError for standardized upstream circuit breaking
                raise HardwareMemoryError(
                    f"Task '{self.operation_name}' failed due to system/GPU memory exhaustion: {exc_val}. "
                    f"Cache evicted. Consider downscaling resolution or switching to cloud/quantized execution."
                ) from exc_val

        # Post-execution cleanup if memory usage spiked
        if self.auto_evict:
            mem = psutil.virtual_memory()
            if mem.percent > self.max_ram_pct:
                logger.debug(f"Memory pressure elevated ({mem.percent}%). Triggering garbage collection.")
                self.evict_memory()

        return False  # Do not suppress unhandled non-OOM exceptions

    def _pre_check(self):
        """Verifies that the system is not already under catastrophic memory pressure."""
        mem = psutil.virtual_memory()
        if mem.percent > self.max_ram_pct:
            logger.warning(
                f"High memory pressure detected before '{self.operation_name}': {mem.percent}% RAM used. "
                "Triggering proactive buffer eviction."
            )
            self.evict_memory()

    @classmethod
    def evict_memory(cls):
        """Forces immediate garbage collection and clears PyTorch CUDA/MPS cache if present."""
        gc.collect()
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.ipc_collect()
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                torch.mps.empty_cache()
        except Exception:
            pass
