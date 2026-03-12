"""
相機控制模組

USB 顯微鏡 1920x1080，向右旋轉 90 度符合列印機視角
"""

import cv2
import time
import threading


def calculate_focus_score(image):
    """
    計算對焦分數 (Laplacian variance)

    Args:
        image: BGR 格式的影像

    Returns:
        對焦分數，越高越清晰
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    return laplacian.var()


class CameraSource:
    """Singleton camera manager with background frame grabbing and auto-reconnect."""

    def __init__(self, device=0, width=1920, height=1080):
        self.device = device
        self.width = width
        self.height = height
        self.cap = None
        self.lock = threading.Lock()
        self.latest_frame = None
        self.connected = False
        self._running = True
        self._thread = threading.Thread(target=self._grab_loop, daemon=True)
        self._thread.start()

    def _open(self):
        cap = cv2.VideoCapture(self.device)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        return cap

    def _grab_loop(self):
        self.cap = self._open()
        while self._running:
            if self.cap is None or not self.cap.isOpened():
                self.connected = False
                self.latest_frame = None
                time.sleep(2)
                try:
                    self.cap = self._open()
                except Exception:
                    self.cap = None
                continue
            ret, frame = self.cap.read()
            if not ret:
                self.connected = False
                self.cap.release()
                self.cap = None
                continue
            self.connected = True
            with self.lock:
                self.latest_frame = frame

    def get_frame(self, rotate=True):
        """Get latest frame for streaming (non-blocking)."""
        with self.lock:
            if self.latest_frame is None:
                return None
            frame = self.latest_frame.copy()
        if rotate:
            frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
        return frame

    def capture(self, discard_frames=5, rotate=True):
        """Capture a high-quality frame for scanning (blocks briefly)."""
        if self.cap is None or not self.cap.isOpened():
            return None
        with self.lock:
            for _ in range(discard_frames):
                self.cap.read()
            ret, frame = self.cap.read()
        if ret and rotate:
            frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
        return frame if ret else None

    def capture_with_score(self, discard_frames=5, rotate=True):
        """Capture frame and return (frame, focus_score)."""
        frame = self.capture(discard_frames, rotate)
        if frame is not None:
            score = calculate_focus_score(frame)
            return frame, score
        return None, 0

    def close(self):
        self._running = False
        self._thread.join(timeout=5)
        if self.cap:
            self.cap.release()


class Camera:
    """USB microscope camera — can use shared CameraSource or standalone."""

    def __init__(self, device=0, rotate=True, warmup_frames=10, source: CameraSource = None):
        self.rotate = rotate
        self._source = source
        if source:
            self.cap = source.cap  # for compatibility
        else:
            self.cap = cv2.VideoCapture(device)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
            for _ in range(warmup_frames):
                self.cap.read()
                time.sleep(0.1)

    def capture(self, discard_frames=5):
        if self._source:
            return self._source.capture(discard_frames, self.rotate)
        # Existing standalone logic
        for _ in range(discard_frames):
            self.cap.read()
        ret, frame = self.cap.read()
        if ret and self.rotate:
            frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
        return frame if ret else None

    def capture_with_score(self, discard_frames=5):
        if self._source:
            return self._source.capture_with_score(discard_frames, self.rotate)
        frame = self.capture(discard_frames)
        if frame is not None:
            score = calculate_focus_score(frame)
            return frame, score
        return None, 0

    def close(self):
        if not self._source:
            self.cap.release()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
