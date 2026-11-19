from typing import List, Dict, Any
import os

class VideoAnalyzer:
    @staticmethod
    def detect_scenes(video_path: str, threshold: float = 27.0) -> List[Dict[str, Any]]:
        """
        Detect scene cut boundaries and durations using PySceneDetect.
        """
        try:
            from scenedetect import detect, ContentDetector
            scenes = detect(video_path, ContentDetector(threshold=threshold))
            results = []
            for i, (start_time, end_time) in enumerate(scenes):
                results.append({
                    "scene_index": i + 1,
                    "start_sec": round(start_time.get_seconds(), 3),
                    "end_sec": round(end_time.get_seconds(), 3),
                    "duration_sec": round(end_time.get_seconds() - start_time.get_seconds(), 3),
                    "start_frame": start_time.get_frames(),
                    "end_frame": end_time.get_frames()
                })
            return results
        except ImportError:
            print("[VideoAnalyzer] scenedetect not installed.")
            return []

    @staticmethod
    def analyze_audio_rhythm(audio_path: str) -> Dict[str, Any]:
        """
        Extract BPM, beat grid, and onset timestamps for cut synchronization using Librosa.
        """
        try:
            import librosa
            y, sr = librosa.load(audio_path, sr=None)
            tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
            beat_times = librosa.frames_to_time(beat_frames, sr=sr).tolist()

            onset_env = librosa.onset.onset_strength(y=y, sr=sr)
            onset_frames = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr)
            onset_times = librosa.frames_to_time(onset_frames, sr=sr).tolist()

            return {
                "bpm": round(float(tempo), 1),
                "beat_times": [round(t, 3) for t in beat_times],
                "onset_times": [round(t, 3) for t in onset_times]
            }
        except ImportError:
            print("[VideoAnalyzer] librosa not installed.")
            return {"bpm": 120.0, "beat_times": [], "onset_times": []}
