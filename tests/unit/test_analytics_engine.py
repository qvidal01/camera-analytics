"""
Unit tests for the AnalyticsEngine module.
"""


from camera_analytics.core.analytics_engine import AnalyticsEngine, Line, LineCrossingEvent
from camera_analytics.core.detection_engine import Detection
from camera_analytics.core.tracking_engine import Track


def test_add_and_remove_line():
    """Test adding and removing a line for analysis."""
    engine = AnalyticsEngine()
    line = Line(id="line1", x1=0, y1=100, x2=200, y2=100)

    engine.add_line(line)
    assert "line1" in engine._lines

    engine.remove_line("line1")
    assert "line1" not in engine._lines


def test_line_crossing_detection():
    """Test that a line crossing event is correctly detected."""
    engine = AnalyticsEngine()
    line = Line(id="line1", x1=100, y1=0, x2=100, y2=200)
    engine.add_line(line)

    # Create a track that crosses the line
    track = Track(track_id=1, class_name="person")
    track.update(Detection(class_name="person", class_id=0, confidence=0.9, bbox=(50, 50, 90, 90)))
    track.update(Detection(class_name="person", class_id=0, confidence=0.9, bbox=(110, 50, 150, 90)))

    events = engine.update([track])

    assert len(events) == 1
    event = events[0]
    assert isinstance(event, LineCrossingEvent)
    assert event.track_id == 1
    assert event.line_id == "line1"


def test_no_line_crossing():
    """Test that no event is generated when a track does not cross a line."""
    engine = AnalyticsEngine()
    line = Line(id="line1", x1=100, y1=0, x2=100, y2=200)
    engine.add_line(line)

    # Create a track that does not cross the line
    track = Track(track_id=1, class_name="person")
    track.update(Detection(class_name="person", class_id=0, confidence=0.9, bbox=(50, 50, 90, 90)))
    track.update(Detection(class_name="person", class_id=0, confidence=0.9, bbox=(60, 50, 100, 90)))

    events = engine.update([track])
    assert len(events) == 0


def test_track_with_single_detection():
    """Test that a track with only one detection does not cause an error."""
    engine = AnalyticsEngine()
    line = Line(id="line1", x1=100, y1=0, x2=100, y2=200)
    engine.add_line(line)

    # Create a track with only one detection
    track = Track(track_id=1, class_name="person")
    track.update(Detection(class_name="person", class_id=0, confidence=0.9, bbox=(50, 50, 90, 90)))

    events = engine.update([track])
    assert len(events) == 0
