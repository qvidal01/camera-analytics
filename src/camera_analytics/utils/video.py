"""Video processing utilities."""

import logging

import numpy as np

logger = logging.getLogger(__name__)


class VideoProcessor:
    """Utility functions for video processing."""

    @staticmethod
    def resize_frame(frame: np.ndarray, width: int, height: int) -> np.ndarray:
        """Resize frame to specified dimensions."""
        import cv2

        return cv2.resize(frame, (width, height))

    @staticmethod
    def draw_boxes(frame: np.ndarray, detections: list) -> np.ndarray:
        """Draw bounding boxes on frame."""
        import cv2

        annotated = frame.copy()
        for det in detections:
            x1, y1, x2, y2 = det.bbox
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(
                annotated,
                f"{det.class_name} {det.confidence:.2f}",
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                2,
            )
        return annotated
