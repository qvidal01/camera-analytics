"""Analytics engine for generating events from tracks."""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime

from camera_analytics.core.tracking_engine import Track

logger = logging.getLogger(__name__)


@dataclass
class Line:
    """A line defined by two points, used for line-crossing detection."""

    id: str
    x1: int
    y1: int
    x2: int
    y2: int


@dataclass
class LineCrossingEvent:
    """Event triggered when a track crosses a defined line."""

    event_id: str
    timestamp: datetime
    track_id: int
    line_id: str
    class_name: str


class AnalyticsEngine:
    """
    Generates analytics events from object tracks.

    This engine analyzes the trajectories of tracked objects to identify
    significant events like line crossings or zone intrusions.
    """

    def __init__(self):
        """Initialize analytics engine."""
        self._lines: dict[str, Line] = {}
        self._track_history: dict[int, list[tuple]] = {}
        self.latest_events: list[LineCrossingEvent] = []
        logger.info("AnalyticsEngine initialized")

    def add_line(self, line: Line):
        """Add a line for crossing detection."""
        if line.id in self._lines:
            raise ValueError(f"Line with ID {line.id} already exists.")
        self._lines[line.id] = line
        logger.info(f"Added line for analysis: {line.id}")

    def remove_line(self, line_id: str):
        """Remove a line from analysis."""
        if line_id not in self._lines:
            logger.warning(f"Attempted to remove non-existent line: {line_id}")
            return
        del self._lines[line_id]
        logger.info(f"Removed line: {line_id}")

    def get_latest_events(self, limit: int = 100) -> list[LineCrossingEvent]:
        """Get the latest analytics events."""
        return self.latest_events[:limit]

    def update(self, tracks: list[Track]) -> list[LineCrossingEvent]:
        """
        Process tracks and generate analytics events.

        Args:
            tracks: List of active tracks from the TrackingEngine.

        Returns:
            List of generated analytics events.
        """
        events = []
        for track in tracks:
            # We need at least two points in the trajectory to detect a crossing
            if len(track.detections) < 2:
                continue

            prev_point = track.detections[-2].center()
            curr_point = track.detections[-1].center()

            for line in self._lines.values():
                if self._check_line_crossing(prev_point, curr_point, line):
                    event = LineCrossingEvent(
                        event_id=f"lc-{track.track_id}-{line.id}-{int(datetime.now(UTC).timestamp())}",
                        timestamp=datetime.now(UTC),
                        track_id=track.track_id,
                        line_id=line.id,
                        class_name=track.class_name,
                    )
                    events.append(event)
                    logger.info(f"Line crossing detected: {event}")

        # Add new events to the in-memory list
        if events:
            self.latest_events = events + self.latest_events
            # Keep only the last 100 events
            self.latest_events = self.latest_events[:100]

        return events

    def _check_line_crossing(self, p1: tuple, p2: tuple, line: Line) -> bool:
        """
        Check if the segment from p1 to p2 intersects with the line.

        This uses a basic line-segment intersection algorithm.
        """

        def orientation(p, q, r):
            val = (q[1] - p[1]) * (r[0] - q[0]) - (q[0] - p[0]) * (r[1] - q[1])
            if val == 0:
                return 0  # Collinear
            return 1 if val > 0 else 2  # Clockwise or Counterclockwise

        l_p1 = (line.x1, line.y1)
        l_p2 = (line.x2, line.y2)

        o1 = orientation(p1, p2, l_p1)
        o2 = orientation(p1, p2, l_p2)
        o3 = orientation(l_p1, l_p2, p1)
        o4 = orientation(l_p1, l_p2, p2)

        # General case
        if o1 != o2 and o3 != o4:
            return True

        # Special cases for collinear points will be ignored for simplicity,
        # as they are less likely in real-world tracking scenarios and
        # can be complex to handle robustly.

        return False
