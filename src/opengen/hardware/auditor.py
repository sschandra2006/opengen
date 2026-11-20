"""
Hardware Auditor for OpenGen.
Interrogates system RAM, CPU cores, GPU accelerators, VRAM, and power states
with graceful fallbacks across Windows, Linux, and macOS.
"""
import logging
import os
import shutil
import subprocess
from typing import Optional, Tuple
import psutil

from opengen.hardware.models import HardwareProfile, AcceleratorType, HardwareTier

logger = logging.getLogger(__name__)


class HardwareAuditor:
    """Interrogates host hardware capabilities dynamically."""

    @classmethod
    def audit(cls) -> HardwareProfile:
        """Executes a full hardware audit and returns a HardwareProfile."""
        # 1. System Memory (RAM)
        mem = psutil.virtual_memory()
        total_ram_gb = round(mem.total / (1024 ** 3), 2)
        available_ram_gb = round(mem.available / (1024 ** 3), 2)
        used_ram_pct = round(mem.percent, 1)

        # 2. CPU Cores
        physical_cores = psutil.cpu_count(logical=False) or 4
        logical_cores = psutil.cpu_count(logical=True) or (physical_cores * 2)

        # 3. Battery State
        is_battery = False
        try:
            battery = psutil.sensors_battery()
            if battery is not None and not battery.power_plugged:
                is_battery = True
        except Exception:
            pass

        # 4. GPU & Accelerator Detection
        accel_type, gpu_name, total_vram_gb, free_vram_gb, has_nvenc = cls._detect_gpu()

        # Temporary placeholder tier (TierClassifier will resolve final tier)
        return HardwareProfile(
            total_ram_gb=total_ram_gb,
            available_ram_gb=available_ram_gb,
            used_ram_pct=used_ram_pct,
            cpu_count_physical=physical_cores,
            cpu_count_logical=logical_cores,
            accelerator=accel_type,
            gpu_name=gpu_name,
            total_vram_gb=total_vram_gb,
            free_vram_gb=free_vram_gb,
            has_nvenc=has_nvenc,
            is_battery_powered=is_battery,
            assigned_tier=HardwareTier.TIER_1_BUDGET
        )

    @classmethod
    def _detect_gpu(cls) -> Tuple[AcceleratorType, Optional[str], float, float, bool]:
        """Detects GPU presence, VRAM, and hardware encoder capabilities."""
        # Path A: Try PyTorch CUDA if installed
        try:
            import torch
            if torch.cuda.is_available():
                name = torch.cuda.get_device_name(0)
                props = torch.cuda.get_device_properties(0)
                total_gb = round(props.total_memory / (1024 ** 3), 2)
                free_b, total_b = torch.cuda.mem_get_info(0)
                free_gb = round(free_b / (1024 ** 3), 2)
                has_nvenc = "nvidia" in name.lower() or "geforce" in name.lower() or "rtx" in name.lower() or "gtx" in name.lower()
                return AcceleratorType.CUDA, name, total_gb, free_gb, has_nvenc
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                return AcceleratorType.MPS, "Apple Silicon GPU (Metal)", 0.0, 0.0, False
        except Exception:
            pass

        # Path B: Try nvidia-smi CLI (works even without PyTorch installed!)
        if shutil.which("nvidia-smi"):
            try:
                cmd = ["nvidia-smi", "--query-gpu=name,memory.total,memory.free", "--format=csv,noheader,nounits"]
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                if res.returncode == 0 and res.stdout.strip():
                    parts = [p.strip() for p in res.stdout.strip().split(",")]
                    if len(parts) >= 3:
                        name = parts[0]
                        total_mb = float(parts[1])
                        free_mb = float(parts[2])
                        total_gb = round(total_mb / 1024.0, 2)
                        free_gb = round(free_mb / 1024.0, 2)
                        has_nvenc = True
                        return AcceleratorType.CUDA, name, total_gb, free_gb, has_nvenc
            except Exception as e:
                logger.debug(f"nvidia-smi query skipped: {e}")

        # Path C: Fallback to CPU Only
        return AcceleratorType.CPU_ONLY, None, 0.0, 0.0, False
