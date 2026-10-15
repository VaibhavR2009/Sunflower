from __future__ import annotations

import time
from pathlib import Path

import cv2
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python import vision


ROOT = Path(__file__).resolve().parent
MODEL_PATH = ROOT / "face_landmarker.task"

# Camera settings
CAMERA_INDEX = 0
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720

# Tracking settings
MIN_FACE_DETECTION_CONFIDENCE = 0.5
MIN_FACE_PRESENCE_CONFIDENCE = 0.5
MIN_TRACKING_CONFIDENCE = 0.5


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def get_face_box(face_landmarks):
    xs = [landmark.x for landmark in face_landmarks]
    ys = [landmark.y for landmark in face_landmarks]
    return min(xs), min(ys), max(xs), max(ys)


def draw_landmarks(frame, face_landmarks):
    height, width = frame.shape[:2]

    # Draw every other point to keep the live display lighter.
    for i, landmark in enumerate(face_landmarks):
        if i % 2 != 0:
            continue
        x = int(clamp(landmark.x, 0.0, 1.0) * (width - 1))
        y = int(clamp(landmark.y, 0.0, 1.0) * (height - 1))
        cv2.circle(frame, (x, y), 1, (0, 255, 0), -1)


def main() -> None:
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Missing model: {MODEL_PATH}\n"
            "Run .\\download_model.ps1 first."
        )

    options = vision.FaceLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(MODEL_PATH)),
        running_mode=vision.RunningMode.VIDEO,
        num_faces=1,
        min_face_detection_confidence=MIN_FACE_DETECTION_CONFIDENCE,
        min_face_presence_confidence=MIN_FACE_PRESENCE_CONFIDENCE,
        min_tracking_confidence=MIN_TRACKING_CONFIDENCE,
        output_face_blendshapes=False,
        output_facial_transformation_matrixes=True,
    )

    cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
    if not cap.isOpened():
        # Fall back to OpenCV's default backend if DirectShow did not open it.
        cap.release()
        cap = cv2.VideoCapture(CAMERA_INDEX)

    if not cap.isOpened():
        raise RuntimeError(
            "Could not open the camera. Try CAMERA_INDEX = 1, 2, etc."
        )

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

    print("Camera started.")
    print("Press Q to quit.")
    print("Green dots = MediaPipe face landmarks.")

    last_timestamp_ms = 0

    with vision.FaceLandmarker.create_from_options(options) as detector:
        while True:
            ok, frame = cap.read()
            if not ok:
                print("Could not read a camera frame.")
                break

            # Keep the original frame for the detector.
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(
                image_format=mp.ImageFormat.SRGB,
                data=rgb,
            )

            timestamp_ms = max(
                last_timestamp_ms + 1,
                int(time.monotonic() * 1000),
            )
            last_timestamp_ms = timestamp_ms

            result = detector.detect_for_video(mp_image, timestamp_ms)

            display = frame.copy()
            height, width = display.shape[:2]

            # Screen center target.
            center_x = width // 2
            center_y = height // 2
            cv2.drawMarker(
                display,
                (center_x, center_y),
                (255, 255, 255),
                cv2.MARKER_CROSS,
                25,
                2,
            )

            if result.face_landmarks:
                face = result.face_landmarks[0]
                draw_landmarks(display, face)

                min_x, min_y, max_x, max_y = get_face_box(face)
                min_x_px = int(clamp(min_x, 0, 1) * (width - 1))
                min_y_px = int(clamp(min_y, 0, 1) * (height - 1))
                max_x_px = int(clamp(max_x, 0, 1) * (width - 1))
                max_y_px = int(clamp(max_y, 0, 1) * (height - 1))

                face_cx = (min_x + max_x) / 2.0
                face_cy = (min_y + max_y) / 2.0

                target_x = int(clamp(face_cx, 0, 1) * (width - 1))
                target_y = int(clamp(face_cy, 0, 1) * (height - 1))

                error_x = face_cx - 0.5
                error_y = face_cy - 0.5

                cv2.rectangle(
                    display,
                    (min_x_px, min_y_px),
                    (max_x_px, max_y_px),
                    (0, 255, 255),
                    2,
                )
                cv2.circle(display, (target_x, target_y), 8, (0, 0, 255), -1)
                cv2.line(
                    display,
                    (center_x, center_y),
                    (target_x, target_y),
                    (255, 0, 255),
                    2,
                )

                # Values to use later for servo control.
                pan_error = error_x
                tilt_error = error_y

                cv2.putText(
                    display,
                    f"Face center: ({face_cx:.3f}, {face_cy:.3f})",
                    (20, 35),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2,
                )
                cv2.putText(
                    display,
                    f"Error X: {pan_error:+.3f}   Error Y: {tilt_error:+.3f}",
                    (20, 65),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 255),
                    2,
                )
            else:
                cv2.putText(
                    display,
                    "NO FACE",
                    (20, 35),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.9,
                    (0, 0, 255),
                    2,
                )

            cv2.putText(
                display,
                "Q = quit",
                (20, height - 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2,
            )

            cv2.imshow("VB Sunflower - Face Tracking", display)

            if (cv2.waitKey(1) & 0xFF) == ord("q"):
                break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
