"""
Hardware Data Models and Schemas for OpenGen Adaptive Compute.
Defines hardware tiers, accelerators, hardware profiles, and execution policies.
"""
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class HardwareTier(str, Enum):
    TIER_0_POTATO = "tier_0_potato"       # 4-8GB RAM, iGPU/CPU only, 0GB VRAM
    TIER_1_BUDGET = "tier_1_budget"       # 8-16GB RAM, 4-6GB VRAM (e.g. RTX 3050/4050 laptop)
    TIER_2_PRO = "tier_2_pro"             # 16-32GB RAM, 8-12GB VRAM (e.g. RTX 3070/4070/M-Pro)
    TIER_3_STUDIO = "tier_3_studio"       # 32GB+ RAM, 16GB+ VRAM (RTX 3090/4090/A100)


class AcceleratorType(str, Enum):
    CUDA = "cuda"
    MPS = "mps"
    DIRECTML = "directml"
    ROCM = "rocm"
    CPU_ONLY = "cpu"


class HardwareProfile(BaseModel):
    """Snapshot of current host system specifications and resource headroom."""
    total_ram_gb: float = Field(..., description="Total system RAM in Gigabytes")
    available_ram_gb: float = Field(..., description="Currently available system RAM in Gigabytes")
    used_ram_pct: float = Field(default=0.0, description="Percentage of RAM currently used")
    cpu_count_physical: int = Field(default=4, description="Number of physical CPU cores")
    cpu_count_logical: int = Field(default=8, description="Number of logical CPU threads")
    accelerator: AcceleratorType = Field(default=AcceleratorType.CPU_ONLY, description="Detected accelerator")
    gpu_name: Optional[str] = Field(default=None, description="Name of the detected GPU device")
    total_vram_gb: float = Field(default=0.0, description="Total GPU VRAM in Gigabytes")
    free_vram_gb: float = Field(default=0.0, description="Free GPU VRAM in Gigabytes")
    has_nvenc: bool = Field(default=False, description="Whether NVIDIA NVENC hardware video encoder is available")
    is_battery_powered: bool = Field(default=False, description="Whether the laptop is running on battery")
    assigned_tier: HardwareTier = Field(default=HardwareTier.TIER_1_BUDGET, description="Assigned hardware tier")


class AdaptiveExecutionPolicy(BaseModel):
    """Dynamic limits and execution flags calculated for the assigned hardware tier."""
    tier: HardwareTier
    # LLM & Token Budgeting
    max_llm_context: int = Field(default=4096, description="Max prompt context window tokens")
    max_output_tokens: int = Field(default=1536, description="Max generated completion tokens per turn")
    allow_local_llm: bool = Field(default=True, description="Whether local model execution is safe")
    recommended_local_model: str = Field(default="ollama/qwen2.5:7b", description="Recommended local model")
    recommended_remote_model: str = Field(default="gemini/gemini-2.5-flash", description="Recommended remote model")
    
    # Image & Diffusion Settings
    image_max_resolution: int = Field(default=768, description="Max dimension for latent generation (px)")
    image_enable_cpu_offload: bool = Field(default=True, description="Enable sequential CPU offload in Diffusers")
    image_enable_vae_tiling: bool = Field(default=True, description="Enable tiled VAE decoding to save VRAM")
    image_precision: str = Field(default="fp16", description="Weight precision: fp8, fp16, int8, fp32")
    rembg_provider: str = Field(default="cpu", description="rembg execution provider: cpu, directml, cuda")
    
    # Video & Motion Graphics Settings
    video_resolution: str = Field(default="1080x1920", description="Video ad render resolution")
    video_target_fps: int = Field(default=30, description="Video target framerate")
    ffmpeg_threads: int = Field(default=4, description="Threads allocated to FFmpeg")
    ffmpeg_codec: str = Field(default="h264_nvenc", description="Preferred video encoder codec")
    
    # Document & Presentation Settings
    doc_chunk_size: int = Field(default=10, description="Max SKUs/sections per generation turn")
    preferred_doc_extractor: str = Field(default="pymupdf", description="Primary document extractor (pymupdf / docling)")
    max_slides_per_pass: int = Field(default=8, description="Max presentation slides to plan in a single turn")
