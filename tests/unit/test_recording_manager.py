"""
Unit tests for the RecordingManager module.
"""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest

from camera_analytics.config.settings import get_settings
from camera_analytics.core.camera_manager import CameraManager
from camera_analytics.core.recording_manager import RecordingManager


@pytest.fixture
def settings():
    """Fixture to provide application settings."""
    s = get_settings()
    s.recording_path = "/tmp/recordings"
    return s


@pytest.fixture
def mock_camera_manager():
    """Fixture to create a mock CameraManager."""
    manager = MagicMock(spec=CameraManager)

    mock_cam = MagicMock()
    mock_cam.get_resolution = AsyncMock(return_value=(1920, 1080))
    mock_cam.get_fps = AsyncMock(return_value=30.0)

    manager.cameras = {"cam1": mock_cam}
    manager.get_frame = AsyncMock(return_value=np.zeros((1080, 1920, 3), dtype=np.uint8))

    return manager


@pytest.fixture
def recording_manager(settings, mock_camera_manager):
    """Fixture to create a RecordingManager instance."""
    # Patch Path.mkdir to avoid creating directories on the filesystem
    with patch.object(Path, "mkdir"):
        manager = RecordingManager(settings, mock_camera_manager)
        yield manager
        # Clean up any running tasks
        asyncio.run(manager.stop_all_recordings())


@pytest.mark.asyncio
@patch("cv2.VideoWriter")
async def test_start_recording(mock_video_writer, recording_manager):
    """Test starting a new recording."""

    # Mock the VideoWriter to behave as if it opened correctly
    mock_writer_instance = MagicMock()
    mock_writer_instance.isOpened.return_value = True
    mock_video_writer.return_value = mock_writer_instance

    camera_id = "cam1"
    duration = 1  # 1 second for a short test

    await recording_manager.start_recording(camera_id, duration)

    # Allow the task to run
    await asyncio.sleep(0.1)

    assert camera_id in recording_manager._recording_tasks
    assert not recording_manager._recording_tasks[camera_id].done()

    # Verify that VideoWriter was called with correct parameters
    mock_video_writer.assert_called()
    args, _ = mock_video_writer.call_args
    assert "cam1" in args[0]
    assert args[2] == 30.0  # FPS
    assert args[3] == (1920, 1080)  # Resolution

    # Let the recording finish
    await asyncio.sleep(duration)

    assert camera_id not in recording_manager._recording_tasks
    mock_writer_instance.release.assert_called_once()


@pytest.mark.asyncio
async def test_stop_all_recordings(recording_manager):
    """Test stopping all ongoing recordings."""

    # To test this without a real recording, we'll create a dummy task
    dummy_task = asyncio.create_task(asyncio.sleep(5))
    recording_manager._recording_tasks["cam1"] = dummy_task

    await recording_manager.stop_all_recordings()

    assert dummy_task.cancelled()
    assert not recording_manager._recording_tasks
