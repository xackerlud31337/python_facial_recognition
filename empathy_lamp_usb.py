import threading
import time
from dataclasses import dataclass
from typing import Optional

import cv2
from deepface import DeepFace

@dataclass
class SharedState:
    lock: threading.Lock
    latest_frame_bgr: Optional["cv2.Mat"] = None
    current_emotion: str = "neutral"

state = SharedState(lock=threading.Lock())

def lamp_set_color(emotion: str) -> None:
    # Replace later with GPIO / Wi-Fi lamp control
    print(f"[LAMP] emotion={emotion}")

def camera_loop(device_index: int = 0) -> None:
    cap = cv2.VideoCapture(device_index, cv2.CAP_V4L2)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    cap.set(cv2.CAP_PROP_FPS, 30)

    if not cap.isOpened():
        raise RuntimeError("Could not open USB camera. Try device_index=0 or 1.")
    
    cv2.namedWindow(
        "Empathy Lamp (USB) - press q to quit",
        cv2.WINDOW_NORMAL
    )
    cv2.resizeWindow(
        "Empathy Lamp (USB) - press q to quit",
        960, 540
    )   

    while True:
        ok, frame = cap.read()
        if not ok:
            continue

        with state.lock:
            state.latest_frame_bgr = frame.copy()

        cv2.imshow("Empathy Lamp (USB) - press q to quit", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()

def ai_loop(period_s: float = 3.0, ai_width: int = 640) -> None:
    while True:
        time.sleep(period_s)

        with state.lock:
            if state.latest_frame_bgr is None:
                continue
            frame = state.latest_frame_bgr.copy()

        # Downscale for AI speed
        h, w = frame.shape[:2]
        scale = ai_width / float(w)
        new_h = int(h * scale)
        small = cv2.resize(frame, (ai_width, new_h), interpolation=cv2.INTER_AREA)

        rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)

        try:
            result = DeepFace.analyze(
                rgb,
                actions=["emotion"],
                enforce_detection=False,
            )

            dominant = result[0]["dominant_emotion"]

            # 3-emotion output + neutral fallback
            if dominant not in {"happy", "sad", "angry"}:
                dominant = "neutral"

            with state.lock:
                prev = state.current_emotion
                if dominant != prev:
                    state.current_emotion = dominant

            if dominant != prev:
                print(f"[AI] {prev} -> {dominant}")
                lamp_set_color(dominant)

        except Exception as e:
            print(f"[AI] error: {e}")

def main():
    t1 = threading.Thread(target=camera_loop, daemon=True)
    t2 = threading.Thread(target=ai_loop, daemon=True)

    t1.start()
    t2.start()

    while t1.is_alive():
        time.sleep(0.5)

if __name__ == "__main__":
    main()
