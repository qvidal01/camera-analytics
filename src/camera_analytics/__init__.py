"""
Camera Analytics - AI-powered security camera analytics system.

This package provides object detection, tracking, and alerting capabilities
for security camera systems with support for multiple camera types (RTSP, USB, files).
"""

__version__ = "0.1.0"
__author__ = "AIQSO"
__license__ = "MIT"

from camera_analytics.core.camera_manager import CameraManager
from camera_analytics.core.detection_engine import DetectionEngine
from camera_analytics.core.tracking_engine import TrackingEngine
from camera_analytics.core.alert_manager import AlertManager

__all__ = [
    "CameraManager",
    "DetectionEngine",
    "TrackingEngine",
    "AlertManager",
]
