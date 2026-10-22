from __future__ import annotations

import argparse
import time
from pathlib import Path

import cv2
import mediapipe as mp
import serial
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python import vision

from arm_controller import ArmController


ROOT = Path(__file__).resolve().parent
MODEL_PATH = ROOT / "face_landmarker.task"


def send_angles(ser: serial.Serial, pan: float, tilt: float, lift: float) -> None:
    message = f"{pan:.1f},{tilt:.1f},{lift:.1f}\n"
    ser.write(message.encode("ascii"))


def open_camera(index: int) -> cv2.VideoCapture:
    """Open the camera and wait until it actually hands us a frame.

    The first read of a DirectShow capture often returns False if the device
    has been sitting idle, so retry instead of treating it as fatal.
    """
    cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap.release()
        cap = cv2.VideoCapture(index)
    if not cap.isOpened():
        raise RuntimeError("Could not open camera.")

    for _ in range(30):
        ok, _ = cap.read()
        if ok:
            return cap
        time.sleep(0.1)

    cap.release()
    raise RuntimeError("Camera opened but never delivered a frame.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--port", type=str, default=None, help="Arduino COM port, e.g. COM5")
    parser.add_argument("--baud", type=int, default=115200)
    args = parser.parse_args()

    if not MODEL_PATH.exists():
        raise FileNotFoundError("face_landmarker.task is missing. Run download_model.ps1 first.")

    ser = None
    if args.port:
        ser = serial.Serial(args.port, args.baud, timeout=0.1)
        time.sleep(2)
        print(f"Connected to Arduino on {args.port}.")

    controller = ArmController()

    options = vision.FaceLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(MODEL_PATH)),
        running_mode=vision.RunningMode.VIDEO,
        num_faces=1,
        min_face_detection_confidence=0.5,
        min_face_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    last_timestamp_ms = 0

    with vision.FaceLandmarker.create_from_options(options) as detector:
        # Open only after the model is ready, so the capture has not gone idle
        cap = open_camera(args.camera)

        failures = 0
        while True:
            ok, frame = cap.read()
            if not ok:
                failures += 1
                if failures >= 30:
                    print("Camera stopped delivering frames.")
                    break
                time.sleep(0.05)
                continue
            failures = 0

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

            timestamp_ms = max(last_timestamp_ms + 1, int(time.monotonic() * 1000))
            last_timestamp_ms = timestamp_ms
            result = detector.detect_for_video(mp_image, timestamp_ms)

            h, w = frame.shape[:2]
            cv2.drawMarker(frame, (w // 2, h // 2), (255, 255, 255), cv2.MARKER_CROSS, 25, 2)

            if result.face_landmarks:
                face = result.face_landmarks[0]
                xs = [p.x for p in face]
                ys = [p.y for p in face]
                cx = (min(xs) + max(xs)) / 2.0
                cy = (min(ys) + max(ys)) / 2.0

                error_x = cx - 0.5
                error_y = cy - 0.5
                angles = controller.update(error_x, error_y)

                px = int(max(0, min(1, cx)) * (w - 1))
                py = int(max(0, min(1, cy)) * (h - 1))
                cv2.circle(frame, (px, py), 10, (0, 0, 255), -1)
                cv2.line(frame, (w // 2, h // 2), (px, py), (255, 0, 255), 2)

                text = f"Pan {angles.pan:5.1f}  Tilt {angles.tilt:5.1f}  Lift {angles.lift:5.1f}"
                cv2.putText(frame, text, (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 255), 2)

                if ser:
                    send_angles(ser, angles.pan, angles.tilt, angles.lift)

            cv2.imshow("VB Sunflower - Monitor Arm", frame)
            if (cv2.waitKey(1) & 0xFF) == ord("q"):
                break

    cap.release()
    cv2.destroyAllWindows()
    if ser:
        ser.close()


if __name__ == "__main__":
    main()
