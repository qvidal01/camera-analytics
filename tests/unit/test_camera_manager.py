"""Unit tests for camera manager."""

import pytest

from camera_analytics.core.camera_manager import (
    CameraConfig,
    CameraManager,
    CameraType,
    CameraStatus,
)


class TestCameraConfig:
    """Test CameraConfig dataclass."""

    def test_camera_config_creation(self):
        """Test camera config can be created."""
        config = CameraConfig(
            id="cam1",
            name="Test Camera",
            source_type=CameraType.USB,
            source_url="/dev/video0",
        )
        assert config.id == "cam1"
        assert config.name == "Test Camera"
        assert config.fps == 15  # Default value


class TestCameraManager:
    """Test CameraManager class."""

    def test_manager_initialization(self):
        """Test manager can be initialized."""
        manager = CameraManager()
        assert len(manager.cameras) == 0

    @pytest.mark.asyncio
    async def test_add_duplicate_camera_fails(self):
        """Test adding camera with duplicate ID fails."""
        manager = CameraManager()
        config = CameraConfig(
            id="cam1",
            name="Camera 1",
            source_type=CameraType.FILE,
            source_url="test.mp4",
        )

        # First add should work (even if connection fails)
        await manager.add_camera(config)

        # Second add with same ID should raise ValueError
        with pytest.raises(ValueError, match="already exists"):
            await manager.add_camera(config)

    @pytest.mark.asyncio
    async def test_get_nonexistent_camera_status(self):
        """Test getting status of non-existent camera returns None."""
        manager = CameraManager()
        status = await manager.get_camera_status("nonexistent")
        assert status is None

    @pytest.mark.asyncio
    async def test_list_cameras_empty(self):
        """Test listing cameras when none are added."""
        manager = CameraManager()
        cameras = await manager.list_cameras()
        assert len(cameras) == 0
        assert isinstance(cameras, dict)
