"""
Object tracking engine for associating detections across frames.

This module provides multi-object tracking capabilities using algorithms like
Kalman filtering and Re-ID matching to track objects across camera views.
"""

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime

import numpy as np
from scipy.optimize import linear_sum_assignment

from camera_analytics.core.detection_engine import Detection

logger = logging.getLogger(__name__)

def _calculate_iou(bbox1: tuple, bbox2: tuple) -> float:
    """Calculate Intersection over Union (IoU) between two bounding boxes."""
    x1_1, y1_1, x2_1, y2_1 = bbox1
    x1_2, y1_2, x2_2, y2_2 = bbox2

    # Calculate intersection area
    x1_inter = max(x1_1, x1_2)
    y1_inter = max(y1_1, y1_2)
    x2_inter = min(x2_1, x2_2)
    y2_inter = min(y2_1, y2_2)

    inter_area = max(0, x2_inter - x1_inter) * max(0, y2_inter - y1_inter)

    # Calculate union area
    area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
    area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
    union_area = area1 + area2 - inter_area

    if union_area == 0:
        return 0.0

    return inter_area / union_area

@dataclass
class Track:
    """
    Represents a tracked object across multiple frames.

    Attributes:
        track_id: Unique tracking identifier
        class_name: Object class
        detections: List of associated detections
        first_seen: Timestamp of first detection
        last_seen: Timestamp of last detection
        active: Whether track is currently active
        age: Number of frames since last update
        hits: Number of consecutive updates
    """

    track_id: int
    class_name: str
    detections: list[Detection] = field(default_factory=list)
    first_seen: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_seen: datetime = field(default_factory=lambda: datetime.now(UTC))
    active: bool = True
    age: int = 0
    hits: int = 0

    def update(self, detection: Detection) -> None:
        """Update track with new detection."""
        detection.track_id = self.track_id
        self.detections.append(detection)
        self.last_seen = datetime.now(UTC)

    def get_current_bbox(self) -> tuple | None:
        """Get most recent bounding box."""
        return self.detections[-1].bbox if self.detections else None

    def get_trajectory(self) -> list[tuple]:
        """Get list of center points (trajectory)."""
        return [det.center() for det in self.detections]


class TrackingEngine:
    """
    Multi-object tracking engine.

    Tracks objects across frames using IoU matching and Kalman filtering.
    """

    def __init__(
        self,
        max_age: int = 30,
        min_hits: int = 3,
        iou_threshold: float = 0.3,
    ):
        """
        Initialize tracking engine.

        Args:
            max_age: Max frames to keep track alive without detections
            min_hits: Min detections before track is confirmed
            iou_threshold: IoU threshold for association
        """
        self.max_age = max_age
        self.min_hits = min_hits
        self.iou_threshold = iou_threshold
        self._tracks: dict[int, Track] = {}
        self._next_track_id = 1
        logger.info("TrackingEngine initialized")

    def update(self, detections: list[Detection]) -> list[Track]:
        """
        Update tracks with new detections using IoU matching.

        Args:
            detections: List of detections from current frame

        Returns:
            List[Track]: List of active and confirmed tracks
        """
        if not self._tracks:
            # No existing tracks, so create new ones for all detections
            for det in detections:
                self._create_track(det)
            # Fall through to the return statement to respect min_hits
        else:
            # 1. Increment age of all tracks and predict next location
            for track in self._tracks.values():
                track.age += 1
                # For a simple IoU tracker, prediction is just the last bbox
                # A Kalman filter would provide a more accurate prediction here

            # 2. Create cost matrix (negative IoU)
            active_tracks = self.get_active_tracks()
            num_tracks = len(active_tracks)
            num_dets = len(detections)
            iou_matrix = np.zeros((num_tracks, num_dets))

            for t, track in enumerate(active_tracks):
                for d, det in enumerate(detections):
                    if track.get_current_bbox():
                        iou_matrix[t, d] = _calculate_iou(track.get_current_bbox(), det.bbox)

            # 3. Use Hungarian algorithm for optimal assignment
            row_ind, col_ind = linear_sum_assignment(-iou_matrix)

            # 4. Update matched tracks
            matched_track_indices = set()
            matched_det_indices = set()

            for t, d in zip(row_ind, col_ind):
                if iou_matrix[t, d] >= self.iou_threshold:
                    track = active_tracks[t]
                    detection = detections[d]
                    track.update(detection)
                    track.age = 0
                    track.hits += 1
                    matched_track_indices.add(t)
                    matched_det_indices.add(d)

            # 5. Create new tracks for unmatched detections
            unmatched_det_indices = set(range(num_dets)) - matched_det_indices
            for d in unmatched_det_indices:
                self._create_track(detections[d])

            # 6. Mark inactive tracks and remove old ones
            for t, track in enumerate(active_tracks):
                if t not in matched_track_indices:
                    if track.age > self.max_age:
                        track.active = False

        self._tracks = {tid: t for tid, t in self._tracks.items() if t.active}

        # Return tracks that are confirmed (have enough hits)
        return [
            t
            for t in self._tracks.values()
            if t.hits >= self.min_hits
        ]

    def _create_track(self, detection: Detection) -> None:
        """Create a new track from a detection."""
        track = Track(track_id=self._next_track_id, class_name=detection.class_name)
        track.update(detection)
        self._tracks[self._next_track_id] = track
        self._next_track_id += 1
        logger.debug(f"Created new track: {track.track_id}")

    def get_active_tracks(self) -> list[Track]:
        """Get all currently active tracks."""
        return [track for track in self._tracks.values() if track.active]
