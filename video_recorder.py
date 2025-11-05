import os
from typing import Optional


class VideoRecorder:
    """
    Minimal no-op video recorder stub.

    Records nothing but preserves API used by simulator:
    - start_recording()
    - is_recording()
    - add_frame(image_rgb)
    - stop_recording() -> Optional[str]
    - frame_count attribute
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
        try:
            os.makedirs(self.output_path, exist_ok=True)
        except Exception:
            pass

    def start_recording(self) -> None:
        self._recording = True
        self.frame_count = 0

    def is_recording(self) -> bool:
        return self._recording

    def add_frame(self, image_rgb) -> None:
        if not self._recording:
            return
        # No-op: increment frame counter only
        self.frame_count += 1

    def stop_recording(self) -> Optional[str]:
        self._recording = False
        # No-op: return a hypothetical path
        return None


