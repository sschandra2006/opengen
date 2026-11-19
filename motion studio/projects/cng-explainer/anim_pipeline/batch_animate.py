import os
import subprocess
import sys
import time
import cv2

ANIM_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(ANIM_DIR)
ASSETS_DIR = os.path.join(PROJECT_DIR, "assets")
LP_DIR = os.path.join(ANIM_DIR, "LivePortrait")
LP_OUT = os.path.join(ANIM_DIR, "lp_out")
FINAL_PLATES = os.path.join(ANIM_DIR, "final_plates")
AUDIO_DIR = os.path.join(ANIM_DIR, "audio_padded")
DRIVING_DIR = os.path.join(ANIM_DIR, "driving")
VENV_PYTHON = os.path.join(ANIM_DIR, ".venv", "Scripts", "python.exe")

os.makedirs(FINAL_PLATES, exist_ok=True)
os.makedirs(LP_OUT, exist_ok=True)

def verify_mp4(filepath, min_dur=10.0):
    if not os.path.isfile(filepath):
        return False
    cap = cv2.VideoCapture(filepath)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    frames = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
    cap.release()
    dur = frames / fps if fps > 0 else 0
    return dur >= min_dur

def run_scene(scene_num):
    s_name = f"scene{scene_num}"
    final_mp4 = os.path.join(FINAL_PLATES, f"{s_name}.mp4")

    if verify_mp4(final_mp4):
        print(f"[{s_name}] Already rendered and valid ({final_mp4}), skipping.")
        return True

    src_img = os.path.join(ASSETS_DIR, f"{s_name}.jpg")
    drv_mp4 = os.path.join(DRIVING_DIR, f"drive_{s_name}.mp4")
    aud_wav = os.path.join(AUDIO_DIR, f"{s_name}_padded.wav")
    lp_mp4 = os.path.join(LP_OUT, f"{s_name}--drive_{s_name}.mp4")

    print(f"\n=======================================================")
    print(f"Starting {s_name} animation pipeline...")
    print(f"Source: {src_img}")
    print(f"Driving: {drv_mp4}")
    print(f"Audio: {aud_wav}")
    print(f"=======================================================\n")

    # Step 1: LivePortrait
    if not verify_mp4(lp_mp4):
        print(f"[{s_name}] Running LivePortrait inference...")
        t0 = time.time()
        cmd_lp = [
            VENV_PYTHON,
            os.path.join(LP_DIR, "inference.py"),
            "-s", src_img,
            "-d", drv_mp4,
            "-o", LP_OUT,
            "--flag_pasteback",
            "--flag_use_half_precision",
            "--flag_crop_driving_video",
            "--source_max_dim", "1920",
        ]
        res = subprocess.run(cmd_lp, cwd=LP_DIR)
        if res.returncode != 0:
            print(f"[{s_name}] ERROR: LivePortrait failed with code {res.returncode}")
            return False
        print(f"[{s_name}] LivePortrait completed in {time.time() - t0:.1f}s")
    else:
        print(f"[{s_name}] LivePortrait output already exists ({lp_mp4})")

    # Step 2: Wav2Lip Lipsync & Smooth Mask Blend
    print(f"[{s_name}] Running Wav2Lip lip-sync blend...")
    t1 = time.time()
    cmd_lip = [
        VENV_PYTHON,
        os.path.join(ANIM_DIR, "lipsync_blend.py"),
        "--video", lp_mp4,
        "--audio", aud_wav,
        "--out", final_mp4,
    ]
    res_lip = subprocess.run(cmd_lip, cwd=ANIM_DIR)
    if res_lip.returncode != 0:
        print(f"[{s_name}] ERROR: Lip-sync blend failed with code {res_lip.returncode}")
        return False
    print(f"[{s_name}] Lip-sync blend completed in {time.time() - t1:.1f}s")

    # Step 3: Quick inspection snapshot
    check_img = os.path.join(ANIM_DIR, f"{s_name}_face_check.png")
    cmd_ff = [
        "ffmpeg", "-y", "-i", final_mp4,
        "-vf", "fps=0.4,scale=480:-1,tile=3x2:padding=4:color=black",
        "-frames:v", "1", check_img
    ]
    subprocess.run(cmd_ff, stderr=subprocess.DEVNULL)
    print(f"[{s_name}] Saved face check: {check_img}")
    return True

if __name__ == "__main__":
    scenes = [int(x) for x in sys.argv[1:]] if len(sys.argv) > 1 else list(range(2, 8))
    print(f"Running animation pipeline for scenes: {scenes}")
    start_all = time.time()
    for s in scenes:
        ok = run_scene(s)
        if not ok:
            print(f"ABORTING at scene {s}")
            sys.exit(1)
    print(f"\nALL SCENES COMPLETED in {time.time() - start_all:.1f}s!")
