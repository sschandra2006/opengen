import os
import math
import subprocess
import sys
import time
import cv2
import numpy as np

ANIM_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(ANIM_DIR)
ASSETS_DIR = os.path.join(PROJECT_DIR, "assets")
AUDIO_DIR = os.path.join(ANIM_DIR, "audio_padded")
FINAL_PLATES = os.path.join(ANIM_DIR, "final_plates")
HAND_BASE_DIR = os.path.join(ANIM_DIR, "hand_base")
VENV_PYTHON = os.path.join(ANIM_DIR, ".venv", "Scripts", "python.exe")

os.makedirs(FINAL_PLATES, exist_ok=True)
os.makedirs(HAND_BASE_DIR, exist_ok=True)

# Scene-specific hand motion configurations (derived from 1920x1080 plate coordinates)
SCENE_CONFIGS = {
    1: {
        "dur": 16.89,
        "hands": [
            {"hx": 1220.0, "hy": 710.0, "sx": 170.0, "sy": 110.0, "dy_amp": 20.0, "dx_amp": 14.0, "freq": 2.2, "y_max_clamp": 460}
        ]
    },
    2: {
        "dur": 15.40,
        "hands": [
            {"hx": 730.0, "hy": 460.0, "sx": 130.0, "sy": 90.0, "dy_amp": 16.0, "dx_amp": 12.0, "freq": 2.4, "y_max_clamp": 360}
        ]
    },
    3: {
        "dur": 16.99,
        "hands": [
            {"hx": 1150.0, "hy": 690.0, "sx": 160.0, "sy": 120.0, "dy_amp": 15.0, "dx_amp": 10.0, "freq": 2.0, "y_max_clamp": 480}
        ]
    },
    4: {
        "dur": 16.63,
        "hands": [
            {"hx": 1530.0, "hy": 660.0, "sx": 220.0, "sy": 130.0, "dy_amp": 18.0, "dx_amp": -12.0, "freq": 2.3, "y_max_clamp": 450}
        ]
    },
    5: {
        "dur": 16.22,
        "hands": [
            {"hx": 220.0, "hy": 780.0, "sx": 150.0, "sy": 110.0, "dy_amp": 18.0, "dx_amp": 10.0, "freq": 2.1, "y_max_clamp": 480, "phase": 0.0},
            {"hx": 1700.0, "hy": 780.0, "sx": 150.0, "sy": 110.0, "dy_amp": 18.0, "dx_amp": -10.0, "freq": 2.1, "y_max_clamp": 480, "phase": 0.85}
        ]
    },
    6: {
        "dur": 17.32,
        "hands": [
            {"hx": 710.0, "hy": 740.0, "sx": 150.0, "sy": 120.0, "dy_amp": 16.0, "dx_amp": 10.0, "freq": 2.2, "y_max_clamp": 460}
        ]
    },
    7: {
        "dur": 17.66,
        "hands": [
            {"hx": 1260.0, "hy": 840.0, "sx": 170.0, "sy": 120.0, "dy_amp": 20.0, "dx_amp": 14.0, "freq": 2.1, "y_max_clamp": 480}
        ]
    }
}

def generate_hand_motion_video(scene_num):
    s_name = f"scene{scene_num}"
    src_img = os.path.join(ASSETS_DIR, f"{s_name}.jpg")
    out_video = os.path.join(HAND_BASE_DIR, f"{s_name}_hand.mp4")
    cfg = SCENE_CONFIGS[scene_num]
    dur = cfg["dur"]
    fps = 30.0
    n_frames = int(round(fps * dur))

    print(f"[{s_name}] Generating organic hand motion video ({n_frames} frames)...")
    img = cv2.imread(src_img)
    h, w = img.shape[:2]
    grid_y, grid_x = np.mgrid[0:h, 0:w].astype(np.float32)

    # Precompute hand weight masks
    hand_weights = []
    for h_cfg in cfg["hands"]:
        hx, hy = h_cfg["hx"], h_cfg["hy"]
        sx, sy = h_cfg["sx"], h_cfg["sy"]
        dist = ((grid_x - hx) / sx) ** 2 + ((grid_y - hy) / sy) ** 2
        w_mask = np.clip(1.0 - dist, 0.0, 1.0)
        # Suppress any displacement near head region
        clamp_y = h_cfg.get("y_max_clamp", 450)
        head_suppress = np.clip((grid_y - clamp_y) / 60.0, 0.0, 1.0)
        w_mask *= head_suppress
        w_mask = cv2.GaussianBlur(w_mask, (51, 51), 0)
        hand_weights.append((w_mask, h_cfg))

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(out_video, fourcc, fps, (w, h))

    for f in range(n_frames):
        t = f / fps
        map_x = grid_x.copy()
        map_y = grid_y.copy()

        for w_mask, h_cfg in hand_weights:
            freq = h_cfg["freq"]
            phase = h_cfg.get("phase", 0.0)
            dy_amp = h_cfg["dy_amp"]
            dx_amp = h_cfg["dx_amp"]
            dy = -dy_amp * math.sin(t * freq + phase) - (dy_amp * 0.4) * math.sin(t * (freq * 2.1) + phase + 0.5)
            dx = dx_amp * math.cos(t * freq + phase + 0.3) + (dx_amp * 0.35) * math.cos(t * (freq * 2.1) + phase)

            map_x -= w_mask * dx
            map_y -= w_mask * dy

        warped = cv2.remap(img, map_x, map_y, interpolation=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
        writer.write(warped)

    writer.release()
    print(f"[{s_name}] Hand motion video generated: {out_video}")
    return out_video

def run_lipsync_on_scene(scene_num, hand_video):
    s_name = f"scene{scene_num}"
    aud_wav = os.path.join(AUDIO_DIR, f"{s_name}_padded.wav")
    final_mp4 = os.path.join(FINAL_PLATES, f"{s_name}.mp4")

    print(f"[{s_name}] Running Wav2Lip lip-sync (head locked, lips articulated)...")
    t0 = time.time()
    cmd = [
        VENV_PYTHON,
        os.path.join(ANIM_DIR, "lipsync_blend.py"),
        "--video", hand_video,
        "--audio", aud_wav,
        "--out", final_mp4,
    ]
    res = subprocess.run(cmd, cwd=ANIM_DIR)
    if res.returncode != 0:
        raise RuntimeError(f"Wav2Lip failed on {s_name}")
    print(f"[{s_name}] Wav2Lip finished in {time.time() - t0:.1f}s -> {final_mp4}")

    # Copy directly to projects/cng-explainer/assets/sceneN.mp4
    target_asset = os.path.join(ASSETS_DIR, f"{s_name}.mp4")
    import shutil
    shutil.copy2(final_mp4, target_asset)
    print(f"[{s_name}] Copied to assets: {target_asset}")
    return final_mp4

def process_scene(scene_num):
    print(f"\n=======================================================")
    print(f"PROCESSING SCENE {scene_num}: HAND MOTION + LOCKED-HEAD LIPSYNC")
    print(f"=======================================================\n")
    hand_video = generate_hand_motion_video(scene_num)
    final_video = run_lipsync_on_scene(scene_num, hand_video)
    return final_video

if __name__ == "__main__":
    scenes = [int(x) for x in sys.argv[1:]] if len(sys.argv) > 1 else list(range(1, 8))
    for s in scenes:
        process_scene(s)
    print("\nALL SCENES COMPLETED SUCCESSFULLY!")
