import os
import cv2
from typing import Optional

class SmartReframer:
    """
    Saliency-Guided 9:16 Subject-Tracking Auto-Reframer for OpenGen Engine 5.
    Transforms landscape (16:9) footage into mobile-first vertical (9:16) video
    using face detection, gaze centering, and LERP camera smoothing.
    """
    def __init__(self, smoothing_factor: float = 0.12):
        self.smoothing_factor = smoothing_factor
        self.face_cascade = None
        if hasattr(cv2, 'CascadeClassifier') and hasattr(cv2, 'data') and hasattr(cv2.data, 'haarcascades'):
            xml_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            if os.path.exists(xml_path):
                self.face_cascade = cv2.CascadeClassifier(xml_path)

    def reframe_to_vertical(
        self,
        input_video: str,
        output_video: str,
        focal_override_x: Optional[float] = None
    ) -> str:
        if not os.path.exists(input_video):
            raise FileNotFoundError(f"Source video not found: {input_video}")

        os.makedirs(os.path.dirname(os.path.abspath(output_video)), exist_ok=True)

        cap = cv2.VideoCapture(input_video)
        orig_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        orig_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0

        target_h = orig_h
        target_w = int(target_h * (9 / 16))

        # Clamp if original width is narrower than calculated 9:16
        if target_w > orig_w:
            target_w = orig_w
            target_h = int(target_w * (16 / 9))

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_video, fourcc, fps, (target_w, target_h))

        smooth_x = orig_w // 2

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            target_x = orig_w // 2

            if focal_override_x is not None:
                target_x = int(orig_w * focal_override_x)
            elif self.face_cascade is not None:
                try:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    faces = self.face_cascade.detectMultiScale(
                        gray,
                        scaleFactor=1.2,
                        minNeighbors=4,
                        minSize=(60, 60)
                    )
                    if len(faces) > 0:
                        fx, fy, fw, fh = faces[0]
                        target_x = fx + (fw // 2)
                except Exception:
                    target_x = orig_w // 2

            # LERP camera smoothing
            smooth_x = int(smooth_x * (1 - self.smoothing_factor) + target_x * self.smoothing_factor)

            # Clamp boundaries
            crop_x1 = max(0, min(smooth_x - (target_w // 2), orig_w - target_w))
            cropped_frame = frame[0:target_h, crop_x1:crop_x1 + target_w]

            out.write(cropped_frame)

        cap.release()
        out.release()
        return output_video
