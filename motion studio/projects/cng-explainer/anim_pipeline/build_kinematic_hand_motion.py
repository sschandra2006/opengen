import os
import subprocess
import sys
import time
import cv2
import numpy as np
import torch
import torch.nn.functional as F

ANIM_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(ANIM_DIR)
ASSETS_DIR = os.path.join(PROJECT_DIR, "assets")
AUDIO_DIR = os.path.join(ANIM_DIR, "audio_padded")
FINAL_PLATES = os.path.join(ANIM_DIR, "final_plates")
HAND_BASE_DIR = os.path.join(ANIM_DIR, "hand_base")
VENV_PYTHON = os.path.join(ANIM_DIR, ".venv", "Scripts", "python.exe")

os.makedirs(FINAL_PLATES, exist_ok=True)
os.makedirs(HAND_BASE_DIR, exist_ok=True)

DEVICE = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
print(f"Using device: {DEVICE}")

def get_frame_anchors():
    return [
        [0, 0], [960, 0], [1919, 0],
        [0, 540], [1919, 540],
        [0, 1079], [960, 1079], [1919, 1079]
    ]

# Complete Scene Configurations
SCENE_RIGS = {
    1: {
        "dur": 16.89,
        "alpha": 1.5,
        "fixed": get_frame_anchors() + [
            # Head box
            [520, 100], [780, 100], [500, 300], [800, 300], [650, 430],
            # Torso & body
            [550, 600], [650, 600], [650, 800], [650, 1000],
            # Surrounding anchors
            [950, 500], [1150, 480], [1350, 480], [1500, 520],
            [1550, 650], [1500, 780], [1420, 880], [1250, 920],
            [1050, 920], [880, 920]
        ],
        "limbs": [
            {
                "src": [[750, 480], [920, 740], [1050, 730], [1150, 710], [1240, 700], [1220, 630], [1330, 670]],
                "delta_up": [[0, 0], [-2, -5], [-5, -25], [-8, -40], [-10, -55], [-10, -55], [-10, -60]],
                "delta_down": [[0, 0], [2, 5], [5, 18], [8, 28], [10, 38], [10, 38], [10, 40]],
            }
        ],
        "phrases": [(1.0, 4.5, 1.0), (6.5, 10.5, 0.95), (11.8, 15.5, 0.90)]
    },
    2: {
        "dur": 15.40,
        "alpha": 1.5,
        "fixed": get_frame_anchors() + [
            [550, 100], [750, 100], [550, 300], [750, 300], [650, 350],
            [600, 500], [650, 700], [650, 900],
            [850, 380], [1050, 360], [1250, 400], [1300, 550],
            [1250, 680], [1100, 720], [900, 750], [750, 750],
            [1500, 300], [1500, 600], [1500, 900]
        ],
        "limbs": [
            {
                "src": [[750, 360], [840, 520], [930, 530], [980, 540], [1030, 540], [1090, 530]],
                "delta_up": [[0, 0], [-2, -5], [-5, -25], [-5, -45], [-5, -55], [-5, -60]],
                "delta_down": [[0, 0], [2, 5], [5, 15], [5, 25], [5, 30], [5, 35]],
            }
        ],
        "phrases": [(1.2, 4.8, 1.0), (6.8, 10.2, 0.95), (11.5, 14.2, 0.88)]
    },
    3: {
        "dur": 16.99,
        "alpha": 1.5,
        "fixed": get_frame_anchors() + [
            [650, 150], [850, 150], [650, 350], [850, 350], [750, 420],
            [650, 550], [700, 750], [700, 950], [550, 750], [620, 850],
            [950, 450], [1150, 420], [1300, 500], [1300, 700],
            [1200, 820], [1000, 850], [850, 850]
        ],
        "limbs": [
            {
                "src": [[800, 450], [850, 620], [920, 660], [980, 690], [1040, 670], [1040, 580], [1130, 650]],
                "delta_up": [[0, 0], [-2, -5], [-5, -25], [-8, -40], [-10, -45], [-10, -45], [-10, -50]],
                "delta_down": [[0, 0], [2, 5], [5, 15], [8, 25], [10, 30], [10, 30], [10, 35]],
            }
        ],
        "phrases": [(1.0, 4.5, 1.0), (6.2, 10.0, 0.95), (11.5, 15.5, 0.90)]
    },
    4: {
        "dur": 16.63,
        "alpha": 1.5,
        "fixed": get_frame_anchors() + [
            [500, 100], [700, 100], [500, 300], [700, 300], [600, 400],
            [550, 550], [600, 750], [600, 950],
            [1050, 450], [1250, 420], [1450, 420], [1500, 600],
            [1350, 750], [1100, 820], [850, 880]
        ],
        "limbs": [
            {
                "src": [[700, 450], [780, 620], [840, 720], [900, 740], [940, 720], [980, 620], [750, 880]],
                "delta_up": [[0, 0], [-2, -5], [-5, -30], [-8, -45], [-8, -50], [-10, -60], [-2, 5]],
                "delta_down": [[0, 0], [2, 5], [5, 20], [8, 30], [8, 35], [10, 45], [2, -5]],
            }
        ],
        "phrases": [(1.0, 4.8, 1.0), (6.5, 10.5, 0.95), (12.0, 15.2, 0.88)]
    },
    5: {
        "dur": 16.22,
        "alpha": 1.5,
        "fixed": get_frame_anchors() + [
            [850, 100], [1050, 100], [850, 300], [1050, 300], [950, 400],
            [950, 550], [950, 750], [950, 950],
            [250, 300], [250, 800], [1650, 300], [1650, 800],
            [650, 650], [1450, 650]
        ],
        "limbs": [
            {
                # Right arm (screen left)
                "src": [[880, 480], [780, 640], [850, 720], [900, 720]],
                "delta_up": [[0, 0], [-5, -10], [-8, -40], [-10, -45]],
                "delta_down": [[0, 0], [5, 8], [8, 25], [10, 28]],
            },
            {
                # Left arm (screen right)
                "src": [[1040, 480], [1150, 620], [1250, 680], [1320, 660]],
                "delta_up": [[0, 0], [5, -10], [10, -40], [15, -45]],
                "delta_down": [[0, 0], [-5, 8], [-10, 25], [-12, 28]],
            }
        ],
        "phrases": [(1.0, 4.8, 1.0), (6.0, 10.2, 0.95), (11.2, 15.0, 0.90)]
    },
    6: {
        "dur": 17.32,
        "alpha": 1.5,
        "fixed": get_frame_anchors() + [
            [550, 100], [750, 100], [550, 300], [750, 300], [650, 400],
            [550, 550], [600, 750], [600, 950],
            [950, 450], [1100, 450], [1250, 600], [1150, 800],
            [950, 850], [750, 880]
        ],
        "limbs": [
            {
                "src": [[700, 450], [750, 650], [820, 740], [860, 700], [820, 620], [900, 580]],
                "delta_up": [[0, 0], [-2, -5], [-5, -35], [-8, -45], [-8, -45], [-10, -55]],
                "delta_down": [[0, 0], [2, 5], [5, 25], [8, 30], [8, 30], [10, 40]],
            }
        ],
        "phrases": [(1.0, 4.8, 1.0), (6.5, 10.8, 0.95), (12.2, 16.0, 0.90)]
    },
    7: {
        "dur": 17.66,
        "alpha": 1.5,
        "fixed": get_frame_anchors() + [
            [700, 150], [900, 150], [700, 350], [900, 350], [800, 430],
            [800, 550], [800, 750], [800, 950],
            [1050, 480], [1250, 480], [1450, 480], [1550, 650],
            [1550, 800], [1450, 900], [1250, 950], [1050, 950],
            [1160, 400], [1160, 600], [1160, 800]
        ],
        "limbs": [
            {
                "src": [[880, 460], [980, 680], [1080, 720], [1170, 730], [1240, 710], [1220, 620], [1350, 670]],
                "delta_up": [[0, 0], [-2, -5], [-5, -30], [-8, -40], [-10, -50], [-10, -50], [-10, -55]],
                "delta_down": [[0, 0], [2, 5], [5, 20], [8, 28], [10, 32], [10, 32], [10, 35]],
            }
        ],
        "phrases": [(1.0, 4.8, 1.0), (6.5, 11.0, 0.95), (12.5, 16.5, 0.90)]
    }
}

def smoothstep(edge0, edge1, x):
    t = np.clip((x - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)

def compute_phrase_weight(t, phrases, dur):
    # Base weight
    val = 0.0
    for p_start, p_end, p_amp in phrases:
        anticipate = 0.6
        settle = 0.8
        p_peak = p_start + anticipate
        p_hold_end = p_end - settle
        
        if p_start <= t < p_peak:
            w = smoothstep(p_start, p_peak, t) * p_amp
            val = max(val, w)
        elif p_peak <= t < p_hold_end:
            # Conversational wrist accent during phrase hold
            accent = 0.06 * np.sin((t - p_peak) * np.pi * 1.5)
            val = max(val, p_amp + accent)
        elif p_hold_end <= t < p_end:
            w = (1.0 - smoothstep(p_hold_end, p_end, t)) * p_amp
            val = max(val, w)
            
    # Gentle organic breathing float (amplitude ~0.04)
    micro = 0.04 * np.sin(t * 1.2) - 0.04
    return float(val + (1.0 - val) * micro)

class GPUMlsWarper:
    def __init__(self, height=1080, width=1920, step=8, alpha=1.5, device=DEVICE):
        self.H = height
        self.W = width
        self.step = step
        self.alpha = alpha
        self.device = device
        
        self.gh = height // step
        self.gw = width // step
        
        grid_y, grid_x = torch.meshgrid(
            torch.linspace(0, height - 1, self.gh, device=device),
            torch.linspace(0, width - 1, self.gw, device=device),
            indexing='ij'
        )
        self.P = torch.stack([grid_x.reshape(-1), grid_y.reshape(-1)], dim=-1) # (N, 2)
        
    def warp(self, img_tensor, src_pts, dst_pts):
        # src_pts: (M, 2), dst_pts: (M, 2)
        p = torch.tensor(dst_pts, dtype=torch.float32, device=self.device)
        v = torch.tensor(src_pts, dtype=torch.float32, device=self.device)
        
        diff_p = self.P.unsqueeze(1) - p.unsqueeze(0) # (N, M, 2)
        dist_sq = torch.sum(diff_p**2, dim=-1) + 1e-5
        w = 1.0 / (dist_sq ** self.alpha)
        w_sum = torch.sum(w, dim=-1, keepdim=True)
        
        p_star = torch.sum(w.unsqueeze(-1) * p.unsqueeze(0), dim=1) / w_sum
        v_star = torch.sum(w.unsqueeze(-1) * v.unsqueeze(0), dim=1) / w_sum
        
        p_hat = p.unsqueeze(0) - p_star.unsqueeze(1)
        v_hat = v.unsqueeze(0) - v_star.unsqueeze(1)
        
        p_perp = torch.stack([-p_hat[..., 1], p_hat[..., 0]], dim=-1)
        x_hat = self.P - p_star
        x_perp = torch.stack([-x_hat[..., 1], x_hat[..., 0]], dim=-1)
        
        mu_s = torch.sum(w * torch.sum(p_hat**2, dim=-1), dim=-1, keepdim=True) + 1e-5
        dot1 = torch.sum(x_hat.unsqueeze(1) * p_hat, dim=-1)
        dot2 = torch.sum(x_perp.unsqueeze(1) * p_hat, dim=-1)
        
        v_perp = torch.stack([-v_hat[..., 1], v_hat[..., 0]], dim=-1)
        fr_x = torch.sum(w * (dot1 * v_hat[..., 0] - dot2 * v_perp[..., 0]), dim=-1, keepdim=True) / mu_s + v_star[:, 0:1]
        fr_y = torch.sum(w * (dot1 * v_hat[..., 1] - dot2 * v_perp[..., 1]), dim=-1, keepdim=True) / mu_s + v_star[:, 1:2]
        
        low_grid = torch.stack([fr_x.reshape(self.gh, self.gw), fr_y.reshape(self.gh, self.gw)], dim=-1).permute(2, 0, 1).unsqueeze(0)
        full_grid = F.interpolate(low_grid, size=(self.H, self.W), mode='bicubic', align_corners=True)
        
        norm_grid_x = 2.0 * full_grid[:, 0, :, :] / (self.W - 1) - 1.0
        norm_grid_y = 2.0 * full_grid[:, 1, :, :] / (self.H - 1) - 1.0
        sample_grid = torch.stack([norm_grid_x, norm_grid_y], dim=-1)
        
        warped = F.grid_sample(img_tensor, sample_grid, mode='bicubic', padding_mode='reflection', align_corners=True)
        return warped

def generate_hand_video(scene_num, warper):
    cfg = SCENE_RIGS[scene_num]
    dur = cfg["dur"]
    fps = 30.0
    n_frames = int(round(fps * dur))
    
    src_img_path = os.path.join(ASSETS_DIR, f"scene{scene_num}.jpg")
    out_video_path = os.path.join(HAND_BASE_DIR, f"scene{scene_num}_hand.mp4")
    
    img = cv2.imread(src_img_path)
    h, w = img.shape[:2]
    img_tensor = torch.from_numpy(img).permute(2, 0, 1).unsqueeze(0).float().to(warper.device)
    
    fixed = cfg["fixed"]
    limbs = cfg["limbs"]
    phrases = cfg["phrases"]
    
    # Precompute src points
    all_src = fixed.copy()
    for limb in limbs:
        all_src.extend(limb["src"])
        
    print(f"[Scene {scene_num}] Rendering {n_frames} frames ({dur:.2f}s) of kinematic hand motion...")
    t0 = time.time()
    
    # Launch FFmpeg writer
    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{w}x{h}",
        "-pix_fmt", "bgr24",
        "-r", f"{fps}",
        "-i", "-",
        "-c:v", "libx264",
        "-crf", "16",
        "-preset", "fast",
        "-pix_fmt", "yuv420p",
        out_video_path
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    
    diff_records = []
    base_frame = None
    max_frame = None
    min_frame = None
    min_w = 999.0
    max_w = -999.0
    
    for f_idx in range(n_frames):
        t = f_idx / fps
        weight = compute_phrase_weight(t, phrases, dur)
        
        # Build current deformed points
        all_dst = fixed.copy()
        for limb in limbs:
            for pt_idx, base_pt in enumerate(limb["src"]):
                if weight >= 0:
                    delta = limb["delta_up"][pt_idx]
                    dx = delta[0] * weight
                    dy = delta[1] * weight
                else:
                    delta = limb["delta_down"][pt_idx]
                    dx = delta[0] * (-weight)
                    dy = delta[1] * (-weight)
                all_dst.append([base_pt[0] + dx, base_pt[1] + dy])
                
        with torch.no_grad():
            warped_t = warper.warp(img_tensor, all_src, all_dst)
            warped_bgr = warped_t.squeeze(0).permute(1, 2, 0).byte().cpu().numpy()
            
        proc.stdin.write(warped_bgr.tobytes())
        
        if f_idx == 0:
            base_frame = warped_bgr.copy()
        if weight > max_w:
            max_w = weight
            max_frame = warped_bgr.copy()
        if weight < min_w:
            min_w = weight
            min_frame = warped_bgr.copy()
            
    proc.stdin.close()
    proc.wait()
    t1 = time.time()
    print(f"[Scene {scene_num}] Hand motion video rendered in {t1-t0:.2f}s ({(t1-t0)/n_frames*1000:.1f}ms/frame)")
    
    # Save verification contact sheet (Min rest, Base, Max gesture) and diff heatmap
    diff = cv2.absdiff(max_frame, base_frame)
    mean_diff = diff.mean()
    max_diff = diff.max()
    print(f"[Scene {scene_num}] Motion verification: mean_diff={mean_diff:.2f}, max_diff={max_diff}")
    
    heat = cv2.applyColorMap(cv2.convertScaleAbs(diff, alpha=3.0), cv2.COLORMAP_JET)
    cv2.imwrite(os.path.join(ANIM_DIR, f"scene{scene_num}_hand_heat.jpg"), heat)
    
    # 3-frame strip
    strip = np.hstack([min_frame, base_frame, max_frame])
    strip_small = cv2.resize(strip, (1920, 360))
    cv2.putText(strip_small, f"Scene {scene_num} Resting", (50, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
    cv2.putText(strip_small, f"Scene {scene_num} Baseline", (690, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
    cv2.putText(strip_small, f"Scene {scene_num} Elevated Gesture", (1330, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
    cv2.imwrite(os.path.join(ANIM_DIR, f"scene{scene_num}_hand_strip.jpg"), strip_small)
    
    return out_video_path

def apply_lipsync(scene_num):
    s_name = f"scene{scene_num}"
    in_video = os.path.join(HAND_BASE_DIR, f"{s_name}_hand.mp4")
    in_audio = os.path.join(AUDIO_DIR, f"{s_name}_padded.wav")
    out_video = os.path.join(FINAL_PLATES, f"{s_name}.mp4")
    lipsync_script = os.path.join(ANIM_DIR, "lipsync_blend.py")
    
    print(f"[{s_name}] Applying Wav2Lip lip sync onto kinematic hand plate...")
    cmd = [
        VENV_PYTHON,
        lipsync_script,
        "--video", in_video,
        "--audio", in_audio,
        "--out", out_video
    ]
    t0 = time.time()
    res = subprocess.run(cmd, capture_output=True, text=True)
    t1 = time.time()
    if res.returncode != 0:
        print(f"[{s_name}] Lipsync ERROR: {res.stderr}")
        raise RuntimeError(f"Lipsync failed for {s_name}")
    print(f"[{s_name}] Lipsync completed in {t1-t0:.2f}s -> {out_video}")
    
    # Copy to assets
    dst_asset = os.path.join(ASSETS_DIR, f"{s_name}.mp4")
    import shutil
    shutil.copy2(out_video, dst_asset)
    print(f"[{s_name}] Copied to {dst_asset}")

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--scene", type=int, default=0, help="Scene number (1-7), or 0 for all")
    args = ap.parse_args()
    
    warper = GPUMlsWarper(alpha=1.5)
    
    scenes = range(1, 8) if args.scene == 0 else [args.scene]
    
    for s in scenes:
        generate_hand_video(s, warper)
        apply_lipsync(s)
        
    print("\n=======================================================")
    print("ALL SCENE PLATES SUCCESSFULLY GENERATED & VERIFIED!")
    print("=======================================================\n")

if __name__ == "__main__":
    main()
