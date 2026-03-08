"""
Camera management module for handling video sources.

This module provides functionality to connect to, manage, and stream from various
camera types including RTSP IP cameras, USB webcams, and video files.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class CameraStatus(Enum):
    """Camera connection status."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


class CameraType(Enum):
    """Supported camera types."""

    RTSP = "rtsp"
    USB = "usb"
    FILE = "file"


@dataclass
class CameraConfig:
    """
    Configuration for a camera source.

    Attributes:
        id: Unique camera identifier
        name: Human-readable camera name
        source_type: Type of camera source
        source_url: Connection URL or device path
        fps: Target frames per second
        resolution: Target resolution as (width, height)
        enabled: Whether camera is enabled
    """

    id: str
    name: str
    source_type: CameraType
    source_url: str
    fps: int = 15
    resolution: tuple[int, int] = (1920, 1080)
    enabled: bool = True


class CameraSource(ABC):
    """
    Abstract base class for camera sources.

    All camera types (RTSP, USB, file) implement this interface.
    """

    def __init__(self, config: CameraConfig):
        """
        Initialize camera source.

        Args:
            config: Camera configuration
        """
        self.config = config
        self.status = CameraStatus.DISCONNECTED
        self._capture: Optional[cv2.VideoCapture] = None

    @abstractmethod
    async def connect(self) -> bool:
        """
        Establish connection to camera.

        Returns:
            bool: True if connection successful, False otherwise
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from camera and cleanup resources."""
        pass

    @abstractmethod
    async def read_frame(self) -> Optional[np.ndarray]:
        """
        Read next frame from camera.

        Returns:
            Optional[np.ndarray]: Frame as numpy array (BGR format) or None if unavailable
        """
        pass

    async def get_fps(self) -> float:
        """
        Get actual FPS of camera stream.

        Returns:
            float: Frames per second
        """
        if self._capture:
            return self._capture.get(cv2.CAP_PROP_FPS)
        return 0.0

    async def get_resolution(self) -> tuple[int, int]:
        """
        Get actual resolution of camera stream.

        Returns:
            tuple[int, int]: (width, height) in pixels
        """
        if self._capture:
            width = int(self._capture.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self._capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
            return (width, height)
        return (0, 0)


class RTSPCamera(CameraSource):
    """RTSP IP camera implementation with auto-reconnect."""

    def __init__(self, config: CameraConfig):
        super().__init__(config)
        self._consecutive_failures = 0
        self._max_failures = 10  # Reconnect after this many failed reads

    async def connect(self) -> bool:
        """Connect to RTSP camera stream."""
        try:
            logger.info(f"Connecting to RTSP camera: {self.config.name}")
            self.status = CameraStatus.CONNECTING

            # Use TCP transport for stable RTSP streams
            import os
            os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"

            # Use async wrapper for blocking CV2 call
            loop = asyncio.get_event_loop()
            self._capture = await loop.run_in_executor(
                None, lambda: cv2.VideoCapture(self.config.source_url, cv2.CAP_FFMPEG)
            )

            if self._capture.isOpened():
                # Minimize internal buffer to get fresher frames
                self._capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                self.status = CameraStatus.CONNECTED
                self._consecutive_failures = 0
                logger.info(f"Successfully connected to {self.config.name}")
                return True
            else:
                self.status = CameraStatus.ERROR
                logger.error(f"Failed to open RTSP stream: {self.config.name}")
                return False

        except Exception as e:
            self.status = CameraStatus.ERROR
            logger.exception(f"Error connecting to RTSP camera {self.config.name}: {e}")
            return False

    async def disconnect(self) -> None:
        """Disconnect from RTSP camera."""
        if self._capture:
            self._capture.release()
            self._capture = None
        self.status = CameraStatus.DISCONNECTED
        logger.info(f"Disconnected from {self.config.name}")

    async def _reconnect(self) -> bool:
        """Reconnect to the RTSP stream."""
        logger.info(f"Reconnecting to {self.config.name}...")
        if self._capture:
            self._capture.release()
            self._capture = None
        return await self.connect()

    async def read_frame(self) -> Optional[np.ndarray]:
        """Read frame from RTSP stream with auto-reconnect and buffer flush."""
        if not self._capture or not self._capture.isOpened():
            # Try to reconnect
            if not await self._reconnect():
                return None

        try:
            loop = asyncio.get_event_loop()

            # Flush the OpenCV internal buffer to get the LATEST frame.
            # OpenCV buffers multiple frames from RTSP streams internally.
            # If we read slower than the stream FPS, we get stale frames
            # that can be seconds or minutes old.
            def _grab_latest():
                # Grab (discard) buffered frames, then read the freshest one
                for _ in range(5):
                    self._capture.grab()
                ret, frame = self._capture.read()
                return ret, frame

            ret, frame = await loop.run_in_executor(None, _grab_latest)

            if ret and frame is not None:
                self._consecutive_failures = 0
                return frame
            else:
                self._consecutive_failures += 1
                if self._consecutive_failures >= self._max_failures:
                    logger.warning(f"{self.config.name}: {self._consecutive_failures} consecutive failures, reconnecting...")
                    self._consecutive_failures = 0
                    await self._reconnect()
                return None

        except Exception as e:
            logger.exception(f"Error reading frame from {self.config.name}: {e}")
            self._consecutive_failures += 1
            if self._consecutive_failures >= self._max_failures:
                await self._reconnect()
            return None


class USBCamera(CameraSource):
    """USB webcam implementation."""

    async def connect(self) -> bool:
        """Connect to USB camera."""
        try:
            logger.info(f"Connecting to USB camera: {self.config.name}")
            self.status = CameraStatus.CONNECTING

            # Try to convert source_url to an integer for device index
            try:
                device_index = int(self.config.source_url)
            except ValueError:
                # If it's not an integer, pass the string directly.
                # OpenCV can handle device paths as strings.
                device_index = self.config.source_url

            loop = asyncio.get_event_loop()
            self._capture = await loop.run_in_executor(None, cv2.VideoCapture, device_index)

            if self._capture.isOpened():
                # Set resolution
                self._capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.resolution[0])
                self._capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.resolution[1])
                self._capture.set(cv2.CAP_PROP_FPS, self.config.fps)

                self.status = CameraStatus.CONNECTED
                logger.info(f"Successfully connected to {self.config.name}")
                return True
            else:
                self.status = CameraStatus.ERROR
                logger.error(f"Failed to open USB camera: {self.config.name}")
                return False

        except Exception as e:
            self.status = CameraStatus.ERROR
            logger.exception(f"Error connecting to USB camera {self.config.name}: {e}")
            return False

    async def disconnect(self) -> None:
        """Disconnect from USB camera."""
        if self._capture:
            self._capture.release()
            self._capture = None
        self.status = CameraStatus.DISCONNECTED
        logger.info(f"Disconnected from {self.config.name}")

    async def read_frame(self) -> Optional[np.ndarray]:
        """Read frame from USB camera."""
        if not self._capture or not self._capture.isOpened():
            return None

        try:
            loop = asyncio.get_event_loop()
            ret, frame = await loop.run_in_executor(None, self._capture.read)

            if ret and frame is not None:
                return frame
            else:
                logger.warning(f"Failed to read frame from {self.config.name}")
                return None

        except Exception as e:
            logger.exception(f"Error reading frame from {self.config.name}: {e}")
            return None


class FileCamera(CameraSource):
    """Video file camera implementation."""

    async def connect(self) -> bool:
        """Open video file."""
        try:
            logger.info(f"Opening video file: {self.config.name}")
            self.status = CameraStatus.CONNECTING

            loop = asyncio.get_event_loop()
            self._capture = await loop.run_in_executor(
                None, cv2.VideoCapture, self.config.source_url
            )

            if self._capture.isOpened():
                self.status = CameraStatus.CONNECTED
                logger.info(f"Successfully opened {self.config.name}")
                return True
            else:
                self.status = CameraStatus.ERROR
                logger.error(f"Failed to open video file: {self.config.name}")
                return False

        except Exception as e:
            self.status = CameraStatus.ERROR
            logger.exception(f"Error opening video file {self.config.name}: {e}")
            return False

    async def disconnect(self) -> None:
        """Close video file."""
        if self._capture:
            self._capture.release()
            self._capture = None
        self.status = CameraStatus.DISCONNECTED
        logger.info(f"Closed {self.config.name}")

    async def read_frame(self) -> Optional[np.ndarray]:
        """Read frame from video file."""
        if not self._capture or not self._capture.isOpened():
            return None

        try:
            loop = asyncio.get_event_loop()
            ret, frame = await loop.run_in_executor(None, self._capture.read)

            if ret and frame is not None:
                return frame
            else:
                # Reached end of file, loop back to start
                self._capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
                logger.debug(f"Looping video file {self.config.name}")
                return None

        except Exception as e:
            logger.exception(f"Error reading frame from {self.config.name}: {e}")
            return None


class CameraManager:
    """
    Manages multiple camera sources.

    This class handles camera lifecycle (connect, disconnect, reconnect),
    frame reading, and camera pool management.
    """

    def __init__(self):
        """Initialize camera manager."""
        self.cameras: Dict[str, CameraSource] = {}
        self._tasks: Dict[str, asyncio.Task] = {}
        logger.info("CameraManager initialized")

    async def add_camera(self, config: CameraConfig) -> bool:
        """
        Add and connect to a new camera.

        Args:
            config: Camera configuration

        Returns:
            bool: True if camera added and connected successfully

        Raises:
            ValueError: If camera with same ID already exists
        """
        if config.id in self.cameras:
            raise ValueError(f"Camera with ID {config.id} already exists")

        # Create appropriate camera source based on type
        camera: CameraSource
        if config.source_type == CameraType.RTSP:
            camera = RTSPCamera(config)
        elif config.source_type == CameraType.USB:
            camera = USBCamera(config)
        elif config.source_type == CameraType.FILE:
            camera = FileCamera(config)
        else:
            raise ValueError(f"Unsupported camera type: {config.source_type}")

        # Attempt connection
        success = await camera.connect()
        if success:
            self.cameras[config.id] = camera
            logger.info(f"Added camera: {config.name} ({config.id})")
        else:
            logger.error(f"Failed to add camera: {config.name}")

        return success

    async def remove_camera(self, camera_id: str) -> None:
        """
        Remove camera and cleanup resources.

        Args:
            camera_id: Camera identifier
        """
        if camera_id not in self.cameras:
            logger.warning(f"Attempted to remove non-existent camera: {camera_id}")
            return

        camera = self.cameras[camera_id]
        await camera.disconnect()
        del self.cameras[camera_id]
        logger.info(f"Removed camera: {camera.config.name} ({camera_id})")

    async def get_frame(self, camera_id: str) -> Optional[np.ndarray]:
        """
        Get current frame from camera.

        Args:
            camera_id: Camera identifier

        Returns:
            Optional[np.ndarray]: Frame or None if unavailable
        """
        if camera_id not in self.cameras:
            logger.warning(f"Attempted to get frame from non-existent camera: {camera_id}")
            return None

        camera = self.cameras[camera_id]
        return await camera.read_frame()

    async def get_camera_status(self, camera_id: str) -> Optional[CameraStatus]:
        """
        Get camera connection status.

        Args:
            camera_id: Camera identifier

        Returns:
            Optional[CameraStatus]: Camera status or None if camera not found
        """
        if camera_id not in self.cameras:
            return None
        return self.cameras[camera_id].status

    async def list_cameras(self) -> Dict[str, Dict]:
        """
        List all cameras with their status.

        Returns:
            Dict[str, Dict]: Dictionary of camera info keyed by camera ID
        """
        result = {}
        for camera_id, camera in self.cameras.items():
            result[camera_id] = {
                "id": camera.config.id,
                "name": camera.config.name,
                "type": camera.config.source_type.value,
                "status": camera.status.value,
                "enabled": camera.config.enabled,
            }
        return result

    async def shutdown(self) -> None:
        """Shutdown all cameras and cleanup resources."""
        logger.info("Shutting down CameraManager")
        for camera_id in list(self.cameras.keys()):
            await self.remove_camera(camera_id)
        logger.info("CameraManager shutdown complete")
