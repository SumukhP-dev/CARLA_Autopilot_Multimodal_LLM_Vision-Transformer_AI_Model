import os
import subprocess
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
        self._ffmpeg_proc: Optional[subprocess.Popen] = None
        self._output_file: Optional[str] = None
        self._writer_file: Optional[str] = None
        self._ffmpeg_path = os.environ.get("FFMPEG_PATH", "ffmpeg")
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
        base_name = f"carla_dashboard_{ts}"
        # Write MJPEG AVI using ffmpeg subprocess for stability
        writer_ext = 'avi'
        self._output_file = os.path.join(self.output_path, f"{base_name}.{writer_ext}")
        self._writer_file = self._output_file

        self._start_ffmpeg_writer()

    def is_recording(self) -> bool:
        return self._recording

    def add_frame(self, image_rgb) -> None:
        if not self._recording or (self._writer is None and self._ffmpeg_proc is None):
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
                # Always capture the full primary monitor for the dashboard view
                monitor = self._sct.monitors[1]
                sct_img = self._sct.grab(monitor)
                dash = np.array(sct_img)[:, :, :3]  # BGRA -> BGR
                dash = cv2.resize(dash, (self.width, self.height))
                # Compose side-by-side: [CARLA | DASHBOARD]
                composed = np.hstack([frame_bgr, dash])
                out_frame = composed
            else:
                out_frame = frame_bgr

            if self._ffmpeg_proc is not None and self._ffmpeg_proc.stdin:
                try:
                    self._ffmpeg_proc.stdin.write(out_frame.tobytes())
                    self.frame_count += 1
                except BrokenPipeError:
                    print("[Video] ERROR: ffmpeg pipe broke during write")
                    self._recording = False
            elif self._writer is not None:
                self._writer.write(out_frame)
                self.frame_count += 1
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
        if self._ffmpeg_proc is not None:
            try:
                if self._ffmpeg_proc.stdin:
                    self._ffmpeg_proc.stdin.close()
                self._ffmpeg_proc.wait(timeout=5)
            except Exception:
                pass
            finally:
                self._ffmpeg_proc = None
        if self._output_file == self._writer_file and self.frame_count == 0 and self._writer_file and os.path.exists(self._writer_file):
            # Remove empty files (no frames)
            os.remove(self._writer_file)
            self._output_file = None
        # Return the path if we actually wrote a file
        return self._output_file

    def _start_ffmpeg_writer(self) -> None:
        """Start an ffmpeg subprocess that accepts raw BGR frames via stdin."""
        cmd = [
            self._ffmpeg_path,
            "-y",
            "-f", "rawvideo",
            "-pix_fmt", "bgr24",
            "-s", f"{self._out_w}x{self._out_h}",
            "-r", str(self.fps),
            "-i", "-",
            "-an",
            "-c:v", "mjpeg",
            "-qscale:v", "3",
            self._writer_file,
        ]
        try:
            self._ffmpeg_proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            if self._ffmpeg_proc.stdin is None:
                raise RuntimeError("Failed to open ffmpeg stdin")
            print("[Video] Using ffmpeg MJPEG pipe for recording")
        except FileNotFoundError:
            print(f"[Video] ERROR: ffmpeg not found at {self._ffmpeg_path}")
            self._ffmpeg_proc = None
            self._recording = False
        except Exception as exc:
            print(f"[Video] ERROR: Unable to start ffmpeg recorder: {exc}")
            self._ffmpeg_proc = None
            self._recording = False

