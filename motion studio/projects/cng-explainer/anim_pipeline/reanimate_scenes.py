import os
import subprocess
import sys
import time

ANIM_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(ANIM_DIR)
ASSETS_DIR = os.path.join(PROJECT_DIR, "assets")
LP_DIR = os.path.join(ANIM_DIR, "LivePortrait")
LP_OUT = os.path.join(ANIM_DIR, "lp_out")
FINAL_PLATES = os.path.join(ANIM_DIR, "final_plates")
AUDIO_DIR = os.path.join(ANIM_DIR, "audio_padded")
DRIVING_DIR = os.path.join(ANIM_DIR, "driving")
VENV_PYTHON = os.path.join(ANIM_DIR, ".venv", "Scripts", "python.exe")

def process_scene(scene_num):
    s_name = f"scene{scene_num}"
    src_img = os.path.join(ASSETS_DIR, f"{s_name}.jpg")
    drv_mp4 = os.path.join(DRIVING_DIR, f"drive_front_{s_name}.mp4")
    aud_wav = os.path.join(AUDIO_DIR, f"{s_name}_padded.wav")
    lp_mp4 = os.path.join(LP_OUT, f"{s_name}--drive_front_{s_name}.mp4")
    final_mp4 = os.path.join(FINAL_PLATES, f"{s_name}.mp4")
    check_png = os.path.join(ANIM_DIR, f"s{scene_num}_front_check.png")

    print(f"\n=======================================================")
    print(f"Re-animating {s_name} with FRONT driving clip...")
    print(f"=======================================================\n")

    # Step 1: LivePortrait
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
        print(f"ERROR: LivePortrait failed on {s_name}")
        return False
    print(f"LivePortrait {s_name} done in {time.time() - t0:.1f}s")

    # Step 2: Lipsync blend
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
        print(f"ERROR: Lipsync blend failed on {s_name}")
        return False
    print(f"Lipsync blend {s_name} done in {time.time() - t1:.1f}s")

    # Step 3: Check sheet
    cmd_ff = [
        "ffmpeg", "-y", "-i", final_mp4,
        "-vf", "fps=0.4,scale=480:-1,tile=3x2:padding=4:color=black",
        "-frames:v", "1", "-update", "1", check_png
    ]
    subprocess.run(cmd_ff, stderr=subprocess.DEVNULL)
    print(f"Check saved: {check_png}")
    return True

if __name__ == "__main__":
    scenes = [4, 5, 7]
    for s in scenes:
        ok = process_scene(s)
        if not ok:
            print(f"Failed at {s}")
            sys.exit(1)
    print("\nALL RE-ANIMATIONS COMPLETED SUCCESSFULLY!")
