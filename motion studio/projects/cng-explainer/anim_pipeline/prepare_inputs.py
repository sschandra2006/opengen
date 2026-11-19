import json
import os
import subprocess
import wave
import numpy as np

PROJECT_DIR = r"f:\motion graphics\motion studio\projects\cng-explainer"
ANIM_DIR = os.path.join(PROJECT_DIR, "anim_pipeline")
REF_VIDEO = r"C:\Users\sscha\.gemini\antigravity\brain\c872ebdb-6d8d-4ebd-bf6d-86d3bfd31cf0\.user_uploaded\media_1794494590662_d392dcdd.mp4"

TIMINGS_PATH = os.path.join(PROJECT_DIR, "src", "scene_timings.json")
with open(TIMINGS_PATH, "r", encoding="utf-8") as f:
    timings = json.load(f)

PAD_AUDIO_DIR = os.path.join(ANIM_DIR, "audio_padded")
DRIVE_DIR = os.path.join(ANIM_DIR, "driving")
os.makedirs(PAD_AUDIO_DIR, exist_ok=True)
os.makedirs(DRIVE_DIR, exist_ok=True)

# Reference video segments where the professor's face is clearly visible for head/blink/pose motion
REF_SEGMENTS = {
    "scene1": (0.8, 12.2),
    "scene2": (18.0, 26.5),
    "scene3": (28.5, 39.5),
    "scene4": (41.5, 49.5),
    "scene5": (56.0, 65.5),
    "scene6": (67.5, 78.0),
    "scene7": (81.5, 91.5),
}


def build_padded_audio(sc):
    sid = sc["id"]
    target_dur = sc["duration"]
    src_wav = os.path.join(PROJECT_DIR, "audio", f"{sid}.wav")
    out_wav = os.path.join(PAD_AUDIO_DIR, f"{sid}_padded.wav")

    with wave.open(src_wav, "rb") as w:
        sr = w.getframerate()
        ch = w.getnchannels()
        pcm = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).reshape(-1, ch)

    lead_samples = int(round(0.40 * sr))
    total_samples = int(round(target_dur * sr))
    pre = np.zeros((lead_samples, ch), dtype=np.int16)
    rem = max(0, total_samples - lead_samples - len(pcm))
    post = np.zeros((rem, ch), dtype=np.int16)
    full = np.vstack([pre, pcm, post])[:total_samples]

    with wave.open(out_wav, "wb") as w:
        w.setnchannels(ch)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(full.tobytes())
    return out_wav


def build_driving_clip(sc):
    sid = sc["id"]
    target_dur = sc["duration"]
    t0, t1 = REF_SEGMENTS[sid]
    out_drive = os.path.join(DRIVE_DIR, f"drive_{sid}.mp4")

    # Extract segment, create smooth forward+reverse ping-pong so head motion loops seamlessly, trim to target_dur at 30fps
    seg_tmp = os.path.join(DRIVE_DIR, f"_seg_{sid}.mp4")
    subprocess.run(
        [
            "ffmpeg", "-y", "-ss", f"{t0:.2f}", "-to", f"{t1:.2f}",
            "-i", REF_VIDEO, "-an", "-r", "30",
            "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p",
            seg_tmp,
        ],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", seg_tmp,
            "-filter_complex",
            f"[0:v]reverse[rev];[0:v][rev]concat=n=2:v=1:a=0,loop=loop=2:size=1000,trim=duration={target_dur:.2f},setpts=PTS-STARTPTS,fps=30[v]",
            "-map", "[v]", "-an",
            "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p",
            out_drive,
        ],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    os.remove(seg_tmp)
    return out_drive


if __name__ == "__main__":
    for sc in timings["scenes"]:
        wa = build_padded_audio(sc)
        dv = build_driving_clip(sc)
        print(f"Prepared {sc['id']}: dur={sc['duration']}s -> {os.path.basename(wa)}, {os.path.basename(dv)}")
