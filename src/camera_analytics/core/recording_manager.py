"""Recording manager for saving video clips."""

import asyncio
import logging
from datetime import UTC, datetime
from pathlib import Path

import cv2

from camera_analytics.config.settings import Settings
from camera_analytics.core.camera_manager import CameraManager

logger = logging.getLogger(__name__)


class RecordingManager:
    """Manages video recording and storage."""

    def __init__(self, settings: Settings, camera_manager: CameraManager):
        """Initialize recording manager."""
        self.settings = settings
        self.camera_manager = camera_manager
        self.storage_path = Path(self.settings.recording_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._recording_tasks: dict[str, asyncio.Task] = {}
        logger.info(f"RecordingManager initialized, storage path: {self.storage_path}")

    async def start_recording(self, camera_id: str, duration: int):
        """
        Start recording a camera for a specific duration.

        If a recording is already in progress for the camera, it will be extended.
        """
        if camera_id in self._recording_tasks and not self._recording_tasks[camera_id].done():
            # Extend recording - for simplicity, we just restart the task
            self._recording_tasks[camera_id].cancel()
            logger.info(f"Extending recording for camera {camera_id}")

        task = asyncio.create_task(self._record_task(camera_id, duration))
        self._recording_tasks[camera_id] = task
        logger.info(f"Started recording for camera {camera_id} for {duration} seconds.")

    async def _record_task(self, camera_id: str, duration: int):
        """The background task that performs the recording."""
        cam = self.camera_manager.cameras.get(camera_id)
        if not cam:
            logger.error(f"Cannot record: camera {camera_id} not found.")
            return

        resolution = await cam.get_resolution()
        fps = await cam.get_fps()
        if fps == 0:
            fps = self.settings.default_fps

        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        filename = f"{camera_id}_{timestamp}.{self.settings.recording_format}"
        filepath = self.storage_path / filename

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(filepath), fourcc, fps, resolution)

        if not writer.isOpened():
            logger.error(f"Failed to open video writer for {filepath}")
            return

        logger.info(f"Recording to {filepath}")

        end_time = asyncio.get_event_loop().time() + duration
        try:
            while asyncio.get_event_loop().time() < end_time:
                frame = await self.camera_manager.get_frame(camera_id)
                if frame is not None:
                    writer.write(frame)
                await asyncio.sleep(1 / fps)
        except asyncio.CancelledError:
            logger.info(f"Recording for camera {camera_id} was cancelled (extended).")
        finally:
            writer.release()
            logger.info(f"Finished recording to {filepath}")
            del self._recording_tasks[camera_id]

    async def stop_all_recordings(self):
        """Stop all ongoing recordings."""
        if not self._recording_tasks:
            return

        logger.info("Stopping all recordings...")
        # Create a copy of tasks to iterate over, as the dict will be modified
        tasks_to_stop = list(self._recording_tasks.values())

        for task in tasks_to_stop:
            task.cancel()

        await asyncio.gather(*tasks_to_stop, return_exceptions=True)

        self._recording_tasks.clear()
        logger.info("All recordings stopped.")
