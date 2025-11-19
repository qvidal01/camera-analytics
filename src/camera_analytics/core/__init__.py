"""Core modules for camera analytics functionality."""

from camera_analytics.core.camera_manager import CameraManager
from camera_analytics.core.detection_engine import DetectionEngine
from camera_analytics.core.tracking_engine import TrackingEngine
from camera_analytics.core.alert_manager import AlertManager
from camera_analytics.core.recording_manager import RecordingManager
from camera_analytics.core.analytics_engine import AnalyticsEngine

__all__ = [
    "CameraManager",
    "DetectionEngine",
    "TrackingEngine",
    "AlertManager",
    "RecordingManager",
    "AnalyticsEngine",
]
