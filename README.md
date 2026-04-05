# Python Facial Recognition / Empathy Lamp USB

This project contains two small Python scripts that use a USB camera with OpenCV:

- `usb_camera_test.py` checks that the camera opens correctly and shows a live preview.
- `empathy_lamp_usb.py` reads frames from the camera, analyzes emotion with DeepFace, and prints a lamp color state based on the detected emotion.

## What Each File Does

### `usb_camera_test.py`

This script:

- opens camera index `0`
- uses the `V4L2` backend
- requests `1920x1080` at `30 FPS`
- shows a live preview window
- exits when you press `q`

Use this first to confirm that the camera is connected and working.

### `empathy_lamp_usb.py`

This script:

- opens camera index `0`
- uses the `V4L2` backend
- requests `1920x1080` at `60 FPS`
- keeps the latest frame in shared memory
- runs emotion analysis every few seconds with `DeepFace`
- maps emotions into `happy`, `neutral`, or `stressed`
- prints a lamp state such as `[LAMP] emotion=happy`

Important: the lamp control is currently a placeholder. The function `lamp_set_color()` only prints output. It does not control real GPIO or a smart lamp yet.

## Important Platform Note

The current code is written for Linux. Both scripts explicitly use `cv2.CAP_V4L2`, which means they expect the Linux `Video4Linux2` camera stack and camera devices such as `/dev/video0`.

If you are on Windows or macOS, the scripts will likely need a small code change to use a different OpenCV camera backend.

## Requirements

### Hardware

- a built-in laptop camera or a USB webcam
- for best results, a UVC-compatible external USB webcam
- a stable USB connection

### Software

- Python 3
- `pip`
- `venv`
- `opencv-python`
- `deepface` for emotion analysis
- Linux `V4L2` camera support
- `v4l-utils` recommended for checking detected camera devices
- usually no separate vendor webcam software is required on Linux if the camera is UVC-compatible

## External USB Camera Setup

If you want to use an external camera, this is the practical setup:

1. Connect the USB camera directly to the computer.
2. If possible, avoid weak adapters or low-power USB hubs.
3. For most modern USB webcams on Linux, no brand-specific driver or app is needed. If the webcam is UVC-compatible, Linux usually detects it automatically.
4. Confirm Linux sees the camera:

```bash
ls /dev/video*
v4l2-ctl --list-devices
```

5. Check the supported formats and resolutions:

```bash
v4l2-ctl -d /dev/video0 --list-formats-ext
```

6. Run the camera test script before running the emotion script.

If your external webcam is not `/dev/video0`, it may appear as `/dev/video1` or `/dev/video2`. In that case, change the camera index from `0` to the correct number in the script.

## Recommended Linux Setup

These commands are a good baseline for Ubuntu, Debian, and Linux Mint.

### 1. Install system packages

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip v4l-utils
```

If OpenCV later fails to import or open a preview window, install these common GUI/runtime libraries too:

```bash
sudo apt install -y libgl1 libglib2.0-0
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

### 3. Install Python dependencies

```bash
pip install opencv-python deepface
```

Note: the first time `DeepFace` runs, it may download model files and take longer to start.

## How To Run

### Test the camera first

```bash
source .venv/bin/activate
python usb_camera_test.py
```

You should see a live camera window. Press `q` to quit.

Run only one script at a time. If `usb_camera_test.py` is still using the webcam, `empathy_lamp_usb.py` may not be able to open it.

### Run the empathy lamp demo

```bash
source .venv/bin/activate
python empathy_lamp_usb.py
```

You should see:

- a live preview window
- terminal messages from the AI loop
- terminal messages from the lamp stub

Example output:

```text
[AI] neutral -> happy
[LAMP] emotion=happy
```

## If Your Camera Is Not Camera 0

Some systems expose the external camera as camera `1` instead of camera `0`.

### In `usb_camera_test.py`

Change:

```python
cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
```

to:

```python
cap = cv2.VideoCapture(1, cv2.CAP_V4L2)
```

### In `empathy_lamp_usb.py`

Change:

```python
def camera_loop(device_index: int = 0) -> None:
```

to:

```python
def camera_loop(device_index: int = 1) -> None:
```

## Troubleshooting

### `Could not open USB camera`

Try the following:

- make sure the camera is connected
- confirm it appears in `v4l2-ctl --list-devices`
- try camera index `1` or `2`
- close other apps that may already be using the camera, such as Zoom, Meet, OBS, or Discord

### `Permission denied` for `/dev/video0`

Add your user to the `video` group and then log out and back in:

```bash
sudo usermod -aG video "$USER"
```

### Camera opens but the image is black or unstable

The requested resolution or FPS may not match what the camera supports. Lower the requested values in the script, for example:

- `1280x720`
- `30 FPS`

### OpenCV window does not appear

Make sure you are running inside a desktop session, not in a headless terminal-only environment. If needed, install:

```bash
sudo apt install -y libgl1 libglib2.0-0
```

### Emotion analysis is slow

That is normal on the first run. `DeepFace` may download model files, and CPU-only emotion analysis can take time.

### Real lamp control does not happen

That is expected in the current version. Replace `lamp_set_color()` with your actual GPIO, serial, or smart-lamp integration.

## Suggested Order Of Use

1. Connect the USB camera.
2. Check detection with `v4l2-ctl --list-devices`.
3. Run `usb_camera_test.py`.
4. If the preview works, run `empathy_lamp_usb.py`.
5. Replace the lamp stub later if you want to control real hardware.
