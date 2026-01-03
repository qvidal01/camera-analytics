"""
Unit tests for the DetectionEngine module.
"""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from camera_analytics.core.detection_engine import Detection, DetectionEngine


@pytest.fixture
def mock_yolo_model():
    """Fixture to mock ultralytics.YOLO model."""
    mock_model = MagicMock()
    mock_model.names = {0: "person", 1: "car"}
    mock_model.to.return_value = None
    mock_model.export.return_value = None

    # Mock the result object structure from ultralytics
    def create_mock_result(*args, **kwargs):
        mock_box = MagicMock()
        mock_box.cls = [0]
        mock_box.conf = [0.95]
        mock_box.xyxy = [[10, 20, 50, 80]]

        mock_result = MagicMock()
        mock_result.boxes = [mock_box]
        mock_result.names = {0: "person", 1: "car"}

        # args[0] is the frame or list of frames
        num_frames = 1
        if isinstance(args[0], list):
            num_frames = len(args[0])

        return [mock_result] * num_frames

    mock_model.side_effect = create_mock_result
    return mock_model


@pytest.fixture


def detection_engine():


    """Fixture to create a DetectionEngine with a mocked model."""


    engine = DetectionEngine()


    return engine








@pytest.mark.asyncio


async def test_load_model_success(detection_engine, mock_yolo_model):


    """Test successful model loading."""


    with patch("camera_analytics.core.detection_engine.YOLO", return_value=mock_yolo_model):


        success = await detection_engine.load_model()





    assert success is True


    assert detection_engine._model is not None


    assert "person" in detection_engine._class_names


    assert "car" in detection_engine._class_names


    mock_yolo_model.to.assert_called_once()








@pytest.mark.asyncio


async def test_load_model_failure(detection_engine):


    """Test model loading failure."""


    with patch("camera_analytics.core.detection_engine.YOLO", side_effect=Exception("Load error")):


        success = await detection_engine.load_model()





    assert success is False


    assert detection_engine._model is None








@pytest.mark.asyncio


async def test_detect_single_frame(detection_engine, mock_yolo_model):


    """Test detecting objects in a single frame."""


    detection_engine._model = mock_yolo_model


    frame = np.zeros((480, 640, 3), dtype=np.uint8)


    detections = await detection_engine.detect(frame)





    assert len(detections) == 1


    detection = detections[0]


    assert isinstance(detection, Detection)


    assert detection.class_name == "person"


    assert detection.confidence > 0.9


    assert detection.bbox == (10, 20, 50, 80)








@pytest.mark.asyncio


async def test_detect_batch(detection_engine, mock_yolo_model):


    """Test detecting objects in a batch of frames."""


    detection_engine._model = mock_yolo_model


    frames = [np.zeros((480, 640, 3), dtype=np.uint8)] * 2


    batch_detections = await detection_engine.detect_batch(frames)





    assert len(batch_detections) == 2


    for detections in batch_detections:


        assert len(detections) == 1


        assert detections[0].class_name == "person"








@pytest.mark.asyncio


async def test_detect_with_class_filter(detection_engine, mock_yolo_model):


    """Test detection with a class filter."""


    detection_engine._model = mock_yolo_model


    frame = np.zeros((480, 640, 3), dtype=np.uint8)


    # The mock result returns a 'person'


    detections = await detection_engine.detect(frame, classes=["car"])


    assert len(detections) == 0





    detections = await detection_engine.detect(frame, classes=["person", "car"])


    assert len(detections) == 1








@pytest.mark.asyncio


async def test_detect_raises_error_if_model_not_loaded(detection_engine):


    """Test that detect raises a RuntimeError if the model is not loaded."""


    frame = np.zeros((480, 640, 3), dtype=np.uint8)


    with pytest.raises(RuntimeError):


        await detection_engine.detect(frame)








@pytest.mark.asyncio


async def test_optimize_model(detection_engine, mock_yolo_model):


    """Test model optimization."""


    detection_engine._model = mock_yolo_model


    success = await detection_engine.optimize_model(export_format="onnx")


    assert success is True


    detection_engine._model.export.assert_called_once_with(


        format="onnx", quantize=False, half=True, device=detection_engine._device_type


    )








def test_get_supported_classes(detection_engine, mock_yolo_model):


    """Test getting the list of supported classes."""


    detection_engine._model = mock_yolo_model


    detection_engine._class_names = list(mock_yolo_model.names.values())


    classes = detection_engine.get_supported_classes()


    assert isinstance(classes, list)


    assert "person" in classes


    assert "car" in classes








def test_get_model_info(detection_engine, mock_yolo_model):


    """Test getting model information."""


    detection_engine._model = mock_yolo_model


    detection_engine._class_names = list(mock_yolo_model.names.values())


    info = detection_engine.get_model_info()


    assert info["model_name"] == "yolov8n"


    assert info["loaded"] is True


    assert info["num_classes"] == 2

