"""
The main processing pipeline of the application.
"""

import asyncio
import logging
from typing import Any

from camera_analytics.core.alert_manager import AlertManager
from camera_analytics.core.analytics_engine import AnalyticsEngine
from camera_analytics.core.camera_manager import CameraManager
from camera_analytics.core.detection_engine import DetectionEngine
from camera_analytics.core.tracking_engine import TrackingEngine

logger = logging.getLogger(__name__)


async def main_pipeline(components: dict[str, Any]):
    """
    The main processing pipeline.
    """
    camera_manager: CameraManager = components["camera_manager"]
    detection_engine: DetectionEngine = components["detection_engine"]
    tracking_engine: TrackingEngine = components["tracking_engine"]
    analytics_engine: AnalyticsEngine = components["analytics_engine"]
    alert_manager: AlertManager = components["alert_manager"]

    logger.info("Main pipeline started.")

    while True:
        try:
            # 1. Get frames from all active cameras
            active_cameras = await camera_manager.list_cameras()
            frames_to_process = []
            camera_ids = []
            for cam_id, cam_info in active_cameras.items():
                if cam_info["enabled"] and cam_info["status"] == "connected":
                    frame = await camera_manager.get_frame(cam_id)
                    if frame is not None:
                        frames_to_process.append(frame)
                        camera_ids.append(cam_id)

            if not frames_to_process:
                await asyncio.sleep(1)
                continue

            # 2. Run detection on the frames
            batch_detections = await detection_engine.detect_batch(frames_to_process)

            # 3. Run tracking and analytics for each camera
            for i, cam_id in enumerate(camera_ids):
                detections = batch_detections[i]

                # 4. Update tracks
                tracks = tracking_engine.update(detections)

                # 5. Run analytics
                events = analytics_engine.update(tracks)

                # 6. Evaluate alerts
                for event in events:
                    await alert_manager.evaluate(event.__dict__)

            await asyncio.sleep(1 / components["settings"].default_fps)

        except asyncio.CancelledError:
            logger.info("Main pipeline cancelled.")
            break
        except Exception as e:
            logger.exception(f"Error in main pipeline: {e}")
            # Avoid crashing the pipeline on an error
            await asyncio.sleep(5)
