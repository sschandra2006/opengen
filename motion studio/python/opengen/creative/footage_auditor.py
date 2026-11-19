import os
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from opengen.ai.providers import AIProviderFactory, BaseAIProvider

class ScoredMicroShot(BaseModel):
    shot_id: str
    start_time: float
    end_time: float
    duration: float
    hook_score: int = Field(ge=1, le=10, description="Intrigue, action, or shock rating (1-10) for opening 3s")
    climax_score: int = Field(ge=1, le=10, description="Product transformation or core payoff intensity (1-10)")
    energy_level: str = Field(description="high | medium | low | dead_pause")
    subject_category: str = Field(description="talking_head | product_demo | user_reaction | b_roll")
    action_summary: str
    focal_center_x: float = Field(ge=0.0, le=1.0, description="Horizontal center of gaze/subject for 9:16 crop")

class DeadZone(BaseModel):
    start_time: float
    end_time: float
    reason: str = Field(description="silent_stare | boring_setup | blur_out_of_focus | redundant")

class FootageAuditReport(BaseModel):
    video_summary: str
    top_hook_candidates: List[ScoredMicroShot]
    top_climax_candidates: List[ScoredMicroShot]
    dead_zones: List[DeadZone] = Field(default_factory=list)
    shots: List[ScoredMicroShot]

class FootageAuditor:
    """
    Multimodal Video Saliency Auditor for OpenGen Engine 5.
    Works with ANY configured AI model (Gemini, OpenAI, Anthropic, Ollama, or Offline CV).
    """
    def __init__(self, provider: Optional[BaseAIProvider] = None):
        self.provider = provider or AIProviderFactory.get_provider()

    def audit_footage(self, video_path: str) -> FootageAuditReport:
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found for audit: {video_path}")

        prompt = """
        You are an elite Direct-Response Video Ad Editor specializing in viral TikTok & Reels ads.
        Analyze every second of this video footage:
        1. Break it down into micro-shots (0.5s to 3.5s).
        2. Score each micro-shot on Hook Potential (1-10) and Climax Intensity (1-10).
        3. Identify all dead pauses, silent stares, and low-energy frames that must be trimmed.
        4. Detect horizontal focal center (0.0 to 1.0) so we can auto-reframe to vertical 9:16.
        """

        raw_data = self.provider.audit_video_saliency(
            video_path=video_path,
            prompt=prompt,
            response_model=FootageAuditReport
        )

        return FootageAuditReport.model_validate(raw_data)
