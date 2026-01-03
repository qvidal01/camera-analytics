"""
Unit tests for the TrackingEngine module.
"""

from camera_analytics.core.detection_engine import Detection
from camera_analytics.core.tracking_engine import TrackingEngine


def test_create_new_tracks():
    """Test that new tracks are created for initial detections."""
    engine = TrackingEngine()
    detections = [
        Detection(class_name="car", class_id=2, confidence=0.9, bbox=(10, 10, 50, 50)),
        Detection(class_name="person", class_id=0, confidence=0.8, bbox=(100, 10, 150, 60)),
    ]

    # On the first update, no tracks are returned as they are not confirmed yet
    tracks = engine.update(detections)
    assert len(tracks) == 0

    # But the tracks should exist in the engine's internal state
    active_tracks = engine.get_active_tracks()
    assert len(active_tracks) == 2
    assert active_tracks[0].track_id == 1
    assert active_tracks[1].track_id == 2


def test_track_matching_with_iou():
    """Test that detections are matched to existing tracks using IoU."""
    engine = TrackingEngine(min_hits=1)

    # First frame
    detections1 = [Detection(class_name="car", class_id=2, confidence=0.9, bbox=(10, 10, 50, 50))]
    tracks = engine.update(detections1)
    assert len(tracks) == 0 # Not confirmed yet

    # Second frame with a slightly moved detection
    detections2 = [Detection(class_name="car", class_id=2, confidence=0.9, bbox=(12, 12, 52, 52))]
    tracks = engine.update(detections2)

    assert len(tracks) == 1
    assert tracks[0].track_id == 1
    assert len(tracks[0].detections) == 2
    assert tracks[0].hits == 1


def test_unmatched_detection_creates_new_track():
    """Test that an unmatched detection creates a new track."""
    engine = TrackingEngine(min_hits=1)

    # First frame
    detections1 = [Detection(class_name="car", class_id=2, confidence=0.9, bbox=(10, 10, 50, 50))]
    engine.update(detections1)

    # Second frame with a new, non-overlapping detection
    detections2 = [Detection(class_name="person", class_id=0, confidence=0.8, bbox=(100, 100, 150, 150))]
    engine.update(detections2)

    # Should have two active tracks now
    active_tracks = engine.get_active_tracks()
    assert len(active_tracks) == 2

    # Check that the new track was created
    new_track = next(t for t in active_tracks if t.track_id == 2)
    assert new_track is not None
    assert new_track.class_name == "person"


def test_unmatched_track_ages_and_is_removed():
    """Test that an unmatched track ages and is eventually removed."""
    engine = TrackingEngine(max_age=2, min_hits=1)

    # Frame 1: Create a track
    detections1 = [Detection(class_name="car", class_id=2, confidence=0.9, bbox=(10, 10, 50, 50))]
    engine.update(detections1)
    assert len(engine.get_active_tracks()) == 1

    # Frame 2: No detections, track should age
    engine.update([])
    track = engine.get_active_tracks()[0]
    assert track.age == 1

    # Frame 3: No detections, track should age again
    engine.update([])
    track = engine.get_active_tracks()[0]
    assert track.age == 2

    # Frame 4: No detections, track should be removed
    engine.update([])
    assert len(engine.get_active_tracks()) == 0


def test_track_confirmation_with_min_hits():
    """Test that a track is only returned after min_hits is reached."""
    engine = TrackingEngine(min_hits=2) # Using 2 for a shorter test

    detections = [Detection(class_name="car", class_id=2, confidence=0.9, bbox=(10, 10, 50, 50))]

    # Update 1 (create track, hits=0)
    tracks = engine.update(detections)
    assert len(tracks) == 0  # Not yet confirmed

    # Update 2 (hits=1)
    tracks = engine.update(detections)
    assert len(tracks) == 0  # Not yet confirmed

    # Update 3 (hits=2, now confirmed)
    tracks = engine.update(detections)
    assert len(tracks) == 1
    assert tracks[0].hits == 2
    assert tracks[0].track_id == 1
