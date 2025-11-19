"""Pytest configuration and shared fixtures."""

import pytest


@pytest.fixture
def sample_frame():
    """Create a sample frame for testing."""
    import numpy as np

    # Create 640x480 RGB image
    return np.zeros((480, 640, 3), dtype=np.uint8)


@pytest.fixture
def sample_detection():
    """Create a sample detection for testing."""
    from camera_analytics.core.detection_engine import Detection

    return Detection(
        class_name="person",
        class_id=0,
        confidence=0.85,
        bbox=(100, 100, 200, 300),
    )
