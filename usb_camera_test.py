import cv2

def main():
    cap = cv2.VideoCapture(0, cv2.CAP_V4L2)  # Brio 100 -> /dev/video0

    # Request 1080p (camera may negotiate a different mode)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    cap.set(cv2.CAP_PROP_FPS, 30)

    if not cap.isOpened():
        raise RuntimeError("Could not open /dev/video0 via V4L2")

    while True:
        ok, frame = cap.read()
        if not ok:
            continue

        cv2.imshow("Brio 100 (q to quit)", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
