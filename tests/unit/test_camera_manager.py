"""
Unit tests for the CameraManager module.
"""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from camera_analytics.core.camera_manager import (
    CameraConfig,
    CameraManager,
    CameraStatus,
    CameraType,
)


@pytest.fixture
def mock_video_capture():
    """Fixture to mock cv2.VideoCapture."""
    mock_capture = MagicMock()
    mock_capture.isOpened.return_value = True
    mock_capture.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
    mock_capture.get.return_value = 30.0  # FPS
    return mock_capture


@pytest.mark.asyncio
async def test_add_rtsp_camera_success(mock_video_capture):
    """Test adding a new RTSP camera successfully."""
    manager = CameraManager()
    config = CameraConfig(
        id="cam1",
        name="Test RTSP Camera",
        source_type=CameraType.RTSP,
        source_url="rtsp://test.url",
    )

    with patch("cv2.VideoCapture", return_value=mock_video_capture):
        success = await manager.add_camera(config)

    assert success is True
    assert "cam1" in manager.cameras
    assert manager.cameras["cam1"].config == config
    assert manager.cameras["cam1"].status == CameraStatus.CONNECTED
    await manager.shutdown()


@pytest.mark.asyncio
async def test_add_usb_camera_success_int_index(mock_video_capture):
    """Test adding a new USB camera successfully with an integer index."""
    manager = CameraManager()
    config = CameraConfig(
        id="cam2",
        name="Test USB Camera",
        source_type=CameraType.USB,
        source_url="0",
    )

    with patch("cv2.VideoCapture", return_value=mock_video_capture) as mock_vc:
        success = await manager.add_camera(config)
        mock_vc.assert_called_with(0)

    assert success is True
    assert "cam2" in manager.cameras
    assert manager.cameras["cam2"].config == config
    assert manager.cameras["cam2"].status == CameraStatus.CONNECTED
    await manager.shutdown()


@pytest.mark.asyncio
async def test_add_usb_camera_success_str_path(mock_video_capture):
    """Test adding a new USB camera successfully with a string path."""
    manager = CameraManager()
    config = CameraConfig(
        id="cam3",
        name="Test USB Camera",
        source_type=CameraType.USB,
        source_url="/dev/video0",
    )

    with patch("cv2.VideoCapture", return_value=mock_video_capture) as mock_vc:
        success = await manager.add_camera(config)
        mock_vc.assert_called_with("/dev/video0")

    assert success is True
    assert "cam3" in manager.cameras
    await manager.shutdown()


@pytest.mark.asyncio
async def test_add_file_camera_success(mock_video_capture):
    """Test adding a new File camera successfully."""
    manager = CameraManager()
    config = CameraConfig(
        id="cam4",
        name="Test File Camera",
        source_type=CameraType.FILE,
        source_url="/path/to/video.mp4",
    )

    with patch("cv2.VideoCapture", return_value=mock_video_capture):
        success = await manager.add_camera(config)

    assert success is True
    assert "cam4" in manager.cameras
    await manager.shutdown()


@pytest.mark.asyncio
async def test_add_camera_failure(mock_video_capture):
    """Test failure when adding a camera."""
    mock_video_capture.isOpened.return_value = False
    manager = CameraManager()
    config = CameraConfig(
        id="cam_fail",
        name="Failed Camera",
        source_type=CameraType.RTSP,
        source_url="rtsp://fail.url",
    )

    with patch("cv2.VideoCapture", return_value=mock_video_capture):
        success = await manager.add_camera(config)

    assert success is False
    assert "cam_fail" not in manager.cameras


@pytest.mark.asyncio
async def test_add_duplicate_camera_raises_error():
    """Test that adding a camera with a duplicate ID raises a ValueError."""
    manager = CameraManager()
    config = CameraConfig(
        id="cam1",
        name="Test Camera",
        source_type=CameraType.FILE,
        source_url="file.mp4",
    )
    with patch("cv2.VideoCapture"):
        await manager.add_camera(config)
        with pytest.raises(ValueError):
            await manager.add_camera(config)

    await manager.shutdown()


@pytest.mark.asyncio
async def test_remove_camera(mock_video_capture):
    """Test removing a camera."""
    manager = CameraManager()
    config = CameraConfig(
        id="cam1", name="Test", source_type=CameraType.FILE, source_url="f.mp4"
    )
    with patch("cv2.VideoCapture", return_value=mock_video_capture):
        await manager.add_camera(config)

    assert "cam1" in manager.cameras
    await manager.remove_camera("cam1")
    assert "cam1" not in manager.cameras
    # Check that release was called
    mock_video_capture.release.assert_called_once()


@pytest.mark.asyncio
async def test_get_frame_success(mock_video_capture):
    """Test getting a frame from a camera."""
    manager = CameraManager()
    config = CameraConfig(
        id="cam1", name="Test", source_type=CameraType.FILE, source_url="f.mp4"
    )
    with patch("cv2.VideoCapture", return_value=mock_video_capture):
        await manager.add_camera(config)

    frame = await manager.get_frame("cam1")
    assert isinstance(frame, np.ndarray)
    assert frame.shape == (480, 640, 3)
    await manager.shutdown()


@pytest.mark.asyncio
async def test_get_frame_nonexistent_camera():
    """Test getting a frame from a camera that does not exist."""
    manager = CameraManager()
    frame = await manager.get_frame("nonexistent")
    assert frame is None


@pytest.mark.asyncio
async def test_list_cameras(mock_video_capture):
    """Test listing cameras."""
    manager = CameraManager()
    config1 = CameraConfig(id="cam1", name="Cam 1", source_type=CameraType.RTSP, source_url="rtsp://1")
    config2 = CameraConfig(id="cam2", name="Cam 2", source_type=CameraType.USB, source_url="0")

    with patch("cv2.VideoCapture", return_value=mock_video_capture):
        await manager.add_camera(config1)
        await manager.add_camera(config2)

    cam_list = await manager.list_cameras()
    assert "cam1" in cam_list
    assert "cam2" in cam_list
    assert cam_list["cam1"]["name"] == "Cam 1"
    assert cam_list["cam2"]["status"] == "connected"
    await manager.shutdown()


@pytest.mark.asyncio
async def test_shutdown(mock_video_capture):
    """Test the shutdown process."""
    manager = CameraManager()
    config1 = CameraConfig(id="cam1", name="Cam 1", source_type=CameraType.RTSP, source_url="rtsp://1")
    config2 = CameraConfig(id="cam2", name="Cam 2", source_type=CameraType.USB, source_url="0")

    with patch("cv2.VideoCapture", return_value=mock_video_capture):
        await manager.add_camera(config1)
        await manager.add_camera(config2)

    await manager.shutdown()
    assert not manager.cameras
    assert mock_video_capture.release.call_count == 2
