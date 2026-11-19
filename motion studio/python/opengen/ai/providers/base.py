import os
import cv2
import base64
import subprocess
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Type, List
from pydantic import BaseModel

class VideoKeyframeExtractor:
    """
    Standardized utility for extracting keyframes and audio stems for vision-based LLMs
    (e.g., OpenAI, Anthropic, Qwen2-VL, Ollama) that do not possess a native video file API.
    """
    @staticmethod
    def extract_keyframes_and_audio(
        video_path: str,
        fps: float = 1.0,
        max_frames: int = 30,
        target_width: int = 720
    ) -> Dict[str, Any]:
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        cap = cv2.VideoCapture(video_path)
        video_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        frame_interval = max(1, int(video_fps / fps))

        frames_data: List[Dict[str, Any]] = []
        frame_idx = 0

        while cap.isOpened() and len(frames_data) < max_frames:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_idx % frame_interval == 0:
                timestamp = round(frame_idx / video_fps, 2)
                h, w = frame.shape[:2]
                target_height = int(h * (target_width / w))
                resized = cv2.resize(frame, (target_width, target_height))
                _, buffer = cv2.imencode('.jpg', resized, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
                b64_str = base64.b64encode(buffer).decode('utf-8')

                frames_data.append({
                    "timestamp": timestamp,
                    "frame_idx": frame_idx,
                    "base64": b64_str
                })

            frame_idx += 1

        cap.release()

        # Extract audio stem if possible
        audio_stem = video_path.rsplit(".", 1)[0] + "_stem.wav"
        try:
            subprocess.run(
                ["ffmpeg", "-y", "-i", video_path, "-vn", "-ac", "1", "-ar", "16000", audio_stem],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False
            )
        except Exception:
            audio_stem = None

        return {
            "frames": frames_data,
            "total_frames_extracted": len(frames_data),
            "audio_stem": audio_stem if (audio_stem and os.path.exists(audio_stem)) else None
        }

class BaseAIProvider(ABC):
    """
    Abstract AI Provider interface for OpenGen.
    Decouples OpenGen from any single model vendor.
    """
    def __init__(self, model_name: Optional[str] = None, api_key: Optional[str] = None):
        self.model_name = model_name
        self.api_key = api_key

    @abstractmethod
    def generate_structured_json(
        self,
        prompt: str,
        system_prompt: str,
        response_model: Optional[Type[BaseModel]] = None,
        temperature: float = 0.2
    ) -> Dict[str, Any]:
        """
        Generate structured, schema-compliant JSON from natural language prompts.
        """
        pass

    @abstractmethod
    def audit_video_saliency(
        self,
        video_path: str,
        prompt: str,
        response_model: Optional[Type[BaseModel]] = None
    ) -> Dict[str, Any]:
        """
        Multimodal video analysis to score hooks, climaxes, gaze/focal centers, and dead zones.
        """
        pass
