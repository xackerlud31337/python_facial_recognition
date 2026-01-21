import threading
import time
from dataclasses import dataclass
from typing import Optional

import cv2
from deepface import DeepFace

STRESS_PAUSE_SECONDS = 30.0

@dataclass
class SharedState:
    lock: threading.Lock
    latest_frame_bgr: Optional["cv2.Mat"] = None
    current_emotion: str = "neutral"
    stressed_pause_until: Optional[float] = None

state = SharedState(lock=threading.Lock())

def lamp_set_color(emotion: str) -> None:
    # Replace later with GPIO / Wi-Fi lamp control
    print(f"[LAMP] emotion={emotion}")

def camera_loop(device_index: int = 0) -> None:
    cap = cv2.VideoCapture(device_index, cv2.CAP_V4L2)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    cap.set(cv2.CAP_PROP_FPS, 60)

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
        now = time.time()

        with state.lock:
            pause_until = state.stressed_pause_until

        if pause_until is not None:
            remaining = pause_until - now
            if remaining > 0:
                print(f"[AI] stressed pause remaining: {int(remaining)}s")
                continue
            with state.lock:
                state.stressed_pause_until = None

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

            # Use probabilities to make stressed easier to trigger
            emotions = result[0].get("emotion", {}) or {}
            dominant_raw = result[0]["dominant_emotion"]

            happy_score = float(emotions.get("happy", 0.0))
            neutral_score = float(emotions.get("neutral", 0.0))
            stressed_score = float(emotions.get("angry", 0.0)) + float(emotions.get("sad", 0.0)) + float(emotions.get("fear", 0.0)) + float(emotions.get("disgust", 0.0))

            top_emotion = max(emotions, key=emotions.get) if emotions else dominant_raw
            top_score = float(emotions.get(top_emotion, 0.0))

            stressed_likely = stressed_score >= 35 or (top_emotion in {"angry", "sad"} and top_score >= 20)

            if stressed_likely:
                dominant = "stressed"
            elif happy_score >= 35 and happy_score >= stressed_score:
                dominant = "happy"
            else:
                dominant = "neutral"
            start_pause = dominant == "stressed"

            with state.lock:
                prev = state.current_emotion
                if dominant != prev:
                    state.current_emotion = dominant
                if start_pause:
                    state.stressed_pause_until = time.time() + STRESS_PAUSE_SECONDS

            if dominant != prev:
                print(f"[AI] {prev} -> {dominant}")
                lamp_set_color(dominant)
            if start_pause:
                print(f"[AI] stressed detected, pausing analysis for {int(STRESS_PAUSE_SECONDS)}s")

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
