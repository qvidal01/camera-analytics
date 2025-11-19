"""Unit tests for detection engine."""

import pytest
import numpy as np

from camera_analytics.core.detection_engine import Detection, DetectionEngine


class TestDetection:
    """Test Detection dataclass."""

    def test_detection_center(self, sample_detection):
        """Test bounding box center calculation."""
        center = sample_detection.center()
        assert center == (150, 200)  # Midpoint of (100,100) and (200,300)

    def test_detection_area(self, sample_detection):
        """Test bounding box area calculation."""
        area = sample_detection.area()
        assert area == 20000  # (200-100) * (300-100)

    def test_detection_to_dict(self, sample_detection):
        """Test conversion to dictionary."""
        result = sample_detection.to_dict()
        assert result["class_name"] == "person"
        assert result["confidence"] == 0.85
        assert result["center"] == (150, 200)


class TestDetectionEngine:
    """Test DetectionEngine class."""

    def test_engine_initialization(self):
        """Test engine can be initialized."""
        engine = DetectionEngine(model_name="yolov8n", device="cpu")
        assert engine.model_name == "yolov8n"
        assert engine.confidence_threshold == 0.5

    def test_confidence_threshold_validation(self):
        """Test confidence threshold must be between 0 and 1."""
        with pytest.raises(ValueError):
            DetectionEngine(confidence_threshold=1.5)

        with pytest.raises(ValueError):
            DetectionEngine(confidence_threshold=-0.1)

    def test_get_supported_classes(self):
        """Test getting supported object classes."""
        engine = DetectionEngine()
        classes = engine.get_supported_classes()
        assert "person" in classes
        assert "car" in classes
        assert len(classes) == 80  # COCO has 80 classes

    @pytest.mark.asyncio
    async def test_detect_without_loaded_model(self, sample_frame):
        """Test detection fails gracefully without loaded model."""
        engine = DetectionEngine()
        with pytest.raises(RuntimeError, match="Model not loaded"):
            await engine.detect(sample_frame)

    def test_get_model_info(self):
        """Test getting model information."""
        engine = DetectionEngine(model_name="yolov8s", device="cuda")
        info = engine.get_model_info()
        assert info["model_name"] == "yolov8s"
        assert info["loaded"] is False
