import os
import time
from datetime import datetime
from typing import Optional

import numpy as np
try:
    import cv2
    CV2_AVAILABLE = True
except Exception:
    CV2_AVAILABLE = False

try:
    import mss  # Optional, for dashboard screen capture
    MSS_AVAILABLE = True
except Exception:
    MSS_AVAILABLE = False


class VideoRecorder:
    """
    Video recorder that writes frames to a video file using OpenCV.

    - When include_dashboard is True and mss is available, captures a screen region
      and composites it side-by-side with the CARLA frame.
    - If OpenCV is unavailable, this recorder becomes a no-op to avoid crashing.
    """

    def __init__(
        self,
        output_path: str = "recordings",
        fps: int = 20,
        width: int = 800,
        height: int = 600,
        include_dashboard: bool = False,
        dashboard_url: str = "http://localhost:4200",
        dashboard_bbox: Optional[tuple] = None,
    ) -> None:
        self.output_path = output_path
        self.fps = fps
        self.width = width
        self.height = height
        self.include_dashboard = include_dashboard
        self.dashboard_url = dashboard_url
        self.dashboard_bbox = dashboard_bbox
        self._recording = False
        self.frame_count = 0
        self._writer = None
        self._output_file: Optional[str] = None
        self._sct = mss.mss() if (include_dashboard and MSS_AVAILABLE) else None
        # Determine output size (double width if including dashboard)
        self._out_w = width * 2 if include_dashboard else width
        self._out_h = height
        try:
            os.makedirs(self.output_path, exist_ok=True)
        except Exception:
            pass

    def start_recording(self) -> None:
        self._recording = True
        self.frame_count = 0
        if not CV2_AVAILABLE:
            return
        # Create output file name
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"carla_dashboard_{ts}.mp4"
        self._output_file = os.path.join(self.output_path, filename)
        # Use MP4V; if not supported on platform, some players may prefer AVI with MJPG
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        try:
            self._writer = cv2.VideoWriter(self._output_file, fourcc, self.fps, (self._out_w, self._out_h))
            if not self._writer.isOpened():
                # Fallback to MJPG AVI
                avi_name = f"carla_dashboard_{ts}.avi"
                self._output_file = os.path.join(self.output_path, avi_name)
                fourcc = cv2.VideoWriter_fourcc(*'MJPG')
                self._writer = cv2.VideoWriter(self._output_file, fourcc, self.fps, (self._out_w, self._out_h))
        except Exception:
            self._writer = None

    def is_recording(self) -> bool:
        return self._recording

    def add_frame(self, image_rgb) -> None:
        if not self._recording:
            return
        self.frame_count += 1
        if not CV2_AVAILABLE:
            return
        try:
            # Ensure numpy array, RGB -> BGR
            frame = np.asarray(image_rgb)
            if frame.ndim == 3 and frame.shape[2] == 4:
                frame = frame[:, :, :3]
            if frame.dtype != np.uint8:
                frame = np.clip(frame, 0, 255).astype(np.uint8)
            frame_bgr = frame[:, :, ::-1]
            # Resize to target size
            frame_bgr = cv2.resize(frame_bgr, (self.width, self.height))

            if self.include_dashboard and self._sct is not None:
                # Capture dashboard region if provided, else capture primary monitor
                if self.dashboard_bbox and all(k in self.dashboard_bbox for k in ("left","top","width","height")):
                    monitor = self.dashboard_bbox
                else:
                    monitor = self._sct.monitors[1]
                sct_img = self._sct.grab(monitor)
                dash = np.array(sct_img)[:, :, :3]  # BGRA -> BGR
                dash = cv2.resize(dash, (self.width, self.height))
                # Compose side-by-side: [CARLA | DASHBOARD]
                composed = np.hstack([frame_bgr, dash])
                out_frame = composed
            else:
                out_frame = frame_bgr

            if self._writer is not None:
                self._writer.write(out_frame)
        except Exception:
            # Swallow errors to avoid breaking the sim loop
            pass

    def stop_recording(self) -> Optional[str]:
        self._recording = False
        if self._writer is not None:
            try:
                self._writer.release()
            except Exception:
                pass
        # Return the path if we actually wrote a file
        return self._output_file


