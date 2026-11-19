"""
Pydantic Data Schemas and Domain Models for Engine 5 (Motion Graphics Studio).
Defines contracts for OpenGen IR v1.1.0, Saliency Auditing, Foley Cues, and Ad Critic Reports.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict


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
    top_hook_candidates: List[ScoredMicroShot] = Field(default_factory=list)
    top_climax_candidates: List[ScoredMicroShot] = Field(default_factory=list)
    dead_zones: List[DeadZone] = Field(default_factory=list)
    shots: List[ScoredMicroShot] = Field(default_factory=list)


class FoleyCue(BaseModel):
    sound: str
    timestamp_sec: float
    volume: float = 0.8


class AdCriticResult(BaseModel):
    passed: bool
    score: int
    violations: List[str] = Field(default_factory=list)
    suggestedRemedies: List[str] = Field(default_factory=list)


class LayerTransform(BaseModel):
    x: Optional[float] = 0
    y: Optional[float] = 0
    scale: Optional[float] = 1.0
    opacity: Optional[float] = 1.0


class LayerAnimation(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    property: str
    from_value: Any = Field(alias="from")
    to_value: Any = Field(alias="to")
    duration: float
    start: float
    easing: Optional[str] = "power2.out"


class MotionLayer(BaseModel):
    id: str
    type: str  # text | image | video | shape | audio
    start: float = 0.0
    duration: float
    zIndex: Optional[int] = 0
    transform: Optional[LayerTransform] = None
    content: Optional[Dict[str, Any]] = None
    animations: Optional[List[LayerAnimation]] = Field(default_factory=list)


class CreativeAdDirectives(BaseModel):
    funnelPhase: Optional[str] = "hook"  # hook | agitation | climax | feature_blitz | cta
    punchIn: Optional[Dict[str, Any]] = None
    audioPunctuation: Optional[Dict[str, Any]] = None
    safeZoneEnforcement: Optional[bool] = True


class MotionScene(BaseModel):
    id: str
    name: Optional[str] = None
    start: float
    duration: float
    backgroundColor: Optional[str] = "#090d16"
    transition: Optional[str] = "cut"
    creativeAdDirectives: Optional[CreativeAdDirectives] = None
    layers: List[MotionLayer] = Field(default_factory=list)


class ProjectSettings(BaseModel):
    width: int = 1080
    height: int = 1920
    fps: int = 30
    aspectRatio: str = "9:16"
    duration: float = 18.0
    backgroundColor: str = "#090d16"


class MotionProjectIR(BaseModel):
    schemaVersion: str = "1.1.0"
    projectId: str
    title: str
    settings: ProjectSettings
    scenes: List[MotionScene] = Field(default_factory=list)
