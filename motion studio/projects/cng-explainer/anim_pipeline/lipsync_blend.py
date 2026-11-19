import argparse
import os
import subprocess
import sys
import cv2
import numpy as np
import torch
from tqdm import tqdm

ANIM_DIR = os.path.dirname(os.path.abspath(__file__))
WAV2LIP_DIR = os.path.join(ANIM_DIR, "Wav2Lip")
sys.path.insert(0, WAV2LIP_DIR)

import audio as w2l_audio  # noqa: E402
import face_detection  # noqa: E402
from models import Wav2Lip  # noqa: E402


def smooth_boxes(boxes, window=5):
    out = boxes.copy()
    for i in range(len(boxes)):
        s = max(0, i - window // 2)
        e = min(len(boxes), i + window // 2 + 1)
        out[i] = np.mean(boxes[s:e], axis=0).astype(int)
    return out


def detect_faces(frames, device, pads=(0, 12, 0, 0), batch_size=16):
    detector = face_detection.FaceAlignment(
        face_detection.LandmarksType._2D, flip_input=False, device=device
    )
    h_img, w_img = frames[0].shape[:2]

    # Step 1: Fast initial face localization on sample frames (downscaled first, native fallback)
    init_box = None
    for sample_idx in [0, len(frames) // 2, len(frames) - 1]:
        frm_rgb = frames[sample_idx][..., ::-1].copy()
        for det_w in [640, 960, w_img]:
            scale = det_w / float(w_img)
            if scale < 0.99:
                probe = cv2.resize(frm_rgb, (det_w, int(h_img * scale)))
            else:
                probe = frm_rgb
            dets = detector.face_detector.detect_from_image(probe)
            if len(dets) > 0:
                best = max(dets, key=lambda d: (d[2] - d[0]) * (d[3] - d[1]) * float(d[4]))
                init_box = [
                    best[0] / scale,
                    best[1] / scale,
                    best[2] / scale,
                    best[3] / scale,
                ]
                break
        if init_box is not None:
            break

    if init_box is None:
        raise RuntimeError("No face detected in sample frames")

    # Step 2: Generous native-resolution ROI around the presenter's face for fast, crisp batch tracking
    fw = init_box[2] - init_box[0]
    fh = init_box[3] - init_box[1]
    pad_roi = int(max(fw, fh) * 0.9)
    rx1 = max(0, int(init_box[0]) - pad_roi)
    ry1 = max(0, int(init_box[1]) - pad_roi)
    rx2 = min(w_img, int(init_box[2]) + pad_roi)
    ry2 = min(h_img, int(init_box[3]) + pad_roi)
    # Keep ROI reasonable in size for S3FD batching
    roi_w, roi_h = rx2 - rx1, ry2 - ry1
    roi_scale = min(1.0, 512.0 / max(roi_w, roi_h))

    preds = []
    for i in tqdm(range(0, len(frames), batch_size), desc="Face detect"):
        crops = []
        for f in frames[i : i + batch_size]:
            c = f[ry1:ry2, rx1:rx2]
            if roi_scale < 0.99:
                c = cv2.resize(c, (int(roi_w * roi_scale), int(roi_h * roi_scale)))
            crops.append(c)
        batch = np.array(crops)
        det_batch = detector.get_detections_for_batch(batch)
        for rect in det_batch:
            if rect is None:
                preds.append(None)
            else:
                preds.append((
                    rx1 + rect[0] / roi_scale,
                    ry1 + rect[1] / roi_scale,
                    rx1 + rect[2] / roi_scale,
                    ry1 + rect[3] / roi_scale,
                ))
    del detector
    torch.cuda.empty_cache()

    boxes = []
    last_good = [
        max(0, int(init_box[0]) - pads[2]),
        max(0, int(init_box[1]) - pads[0]),
        min(w_img, int(init_box[2]) + pads[3]),
        min(h_img, int(init_box[3]) + pads[1]),
    ]
    pady1, pady2, padx1, padx2 = pads
    for rect in preds:
        if rect is None:
            boxes.append(last_good)
        else:
            y1 = max(0, int(rect[1]) - pady1)
            y2 = min(h_img, int(rect[3]) + pady2)
            x1 = max(0, int(rect[0]) - padx1)
            x2 = min(w_img, int(rect[2]) + padx2)
            last_good = [x1, y1, x2, y2]
            boxes.append(last_good)
    boxes = smooth_boxes(np.array(boxes), window=7)
    return boxes


def make_lower_face_mask(w, h):
    """Smooth elliptical mask covering ONLY lower 54% of face box (mouth/jaw/chin), keeping eyes & glasses 100% sharp."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    cx = w * 0.50
    cy = h * 0.69
    rx = w * 0.36
    ry = h * 0.27
    dist = ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2
    mask = np.clip(1.0 - np.maximum(0.0, dist - 0.32) / 0.68, 0.0, 1.0)
    # Suppress upper 46% completely so eyes & glasses stay untouched
    top_ramp = np.clip((yy / h - 0.44) / 0.14, 0.0, 1.0)
    mask *= top_ramp
    k = max(5, (min(w, h) // 10) | 1)
    mask = cv2.GaussianBlur(mask, (k, k), 0)
    return mask[:, :, None]


def sharpen_patch(patch):
    blur = cv2.GaussianBlur(patch, (0, 0), 1.2)
    return np.clip(cv2.addWeighted(patch, 1.28, blur, -0.28, 0), 0, 255).astype(np.uint8)


def load_wav2lip(ckpt_path, device):
    model = Wav2Lip()
    ckpt = torch.load(ckpt_path, map_location="cpu" if device == "cpu" else None)
    state = {k.replace("module.", ""): v for k, v in ckpt["state_dict"].items()}
    model.load_state_dict(state)
    return model.to(device).eval()


def run_lipsync(video_path, audio_path, out_path, ckpt_path):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    frames = []
    while True:
        ok, frm = cap.read()
        if not ok:
            break
        frames.append(frm)
    cap.release()
    if not frames:
        raise RuntimeError(f"Empty video: {video_path}")

    h, w = frames[0].shape[:2]

    # Load wav + tiny dither to guarantee non-NaN mel on silence
    wav = w2l_audio.load_wav(audio_path, 16000)
    rng = np.random.default_rng(123)
    wav = wav + rng.normal(0, 1e-5, size=wav.shape).astype(wav.dtype)
    mel = w2l_audio.melspectrogram(wav)
    if np.isnan(mel).any():
        raise RuntimeError("NaN in mel spectrogram")

    mel_step_size = 16
    mel_idx_mult = 80.0 / fps
    mel_chunks = []
    i = 0
    while True:
        s_idx = int(i * mel_idx_mult)
        if s_idx + mel_step_size > mel.shape[1]:
            mel_chunks.append(mel[:, mel.shape[1] - mel_step_size :])
            break
        mel_chunks.append(mel[:, s_idx : s_idx + mel_step_size])
        i += 1

    # Match frame count cleanly
    n_out = min(len(frames), len(mel_chunks))
    frames = frames[:n_out]
    mel_chunks = mel_chunks[:n_out]

    boxes = detect_faces(frames, device, batch_size=4)
    model = load_wav2lip(ckpt_path, device)

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo", "-vcodec", "rawvideo",
        "-s", f"{w}x{h}", "-pix_fmt", "bgr24", "-r", f"{fps:.3f}",
        "-i", "-",
        "-an",
        "-c:v", "libx264", "-crf", "15", "-pix_fmt", "yuv420p",
        out_path,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)

    batch_size = 32
    img_size = 96
    for b0 in tqdm(range(0, n_out, batch_size), desc="Wav2Lip"):
        b1 = min(n_out, b0 + batch_size)
        img_batch, mel_batch = [], []
        for idx in range(b0, b1):
            x1, y1, x2, y2 = boxes[idx]
            face = cv2.resize(frames[idx][y1:y2, x1:x2], (img_size, img_size))
            img_batch.append(face)
            mel_batch.append(mel_chunks[idx])

        img_arr = np.asarray(img_batch)
        img_masked = img_arr.copy()
        img_masked[:, img_size // 2 :] = 0
        img_in = np.concatenate((img_masked, img_arr), axis=3) / 255.0
        mel_arr = np.asarray(mel_batch).reshape(len(mel_batch), mel_chunks[0].shape[0], mel_chunks[0].shape[1], 1)

        img_t = torch.FloatTensor(np.transpose(img_in, (0, 3, 1, 2))).to(device)
        mel_t = torch.FloatTensor(np.transpose(mel_arr, (0, 3, 1, 2))).to(device)

        with torch.no_grad():
            pred = model(mel_t, img_t).cpu().numpy().transpose(0, 2, 3, 1) * 255.0

        for k_idx, p in enumerate(pred):
            idx = b0 + k_idx
            frm = frames[idx].copy()
            x1, y1, x2, y2 = boxes[idx]
            pw, ph = x2 - x1, y2 - y1
            p_res = cv2.resize(np.clip(p, 0, 255).astype(np.uint8), (pw, ph), interpolation=cv2.INTER_CUBIC)
            p_res = sharpen_patch(p_res)
            mask = make_lower_face_mask(pw, ph)
            orig_crop = frm[y1:y2, x1:x2].astype(np.float32)
            blended = (p_res.astype(np.float32) * mask + orig_crop * (1.0 - mask)).astype(np.uint8)
            frm[y1:y2, x1:x2] = blended
            proc.stdin.write(frm.tobytes())

    proc.stdin.close()
    proc.wait()
    if proc.returncode != 0:
        raise RuntimeError("FFmpeg encode failed")
    print(f"Saved lip-synced video: {out_path} ({n_out} frames)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--audio", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--ckpt", default=os.path.join(WAV2LIP_DIR, "checkpoints", "wav2lip_gan.pth"))
    args = ap.parse_args()
    run_lipsync(args.video, args.audio, args.out, args.ckpt)
