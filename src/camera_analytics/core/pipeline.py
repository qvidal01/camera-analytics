"""
The main processing pipeline of the application.
"""

import asyncio
import logging
from datetime import datetime, UTC
from typing import Dict, Any, List, Optional

from camera_analytics.core.camera_manager import CameraManager
from camera_analytics.core.detection_engine import DetectionEngine
from camera_analytics.core.tracking_engine import TrackingEngine
from camera_analytics.core.analytics_engine import AnalyticsEngine
from camera_analytics.core.alert_manager import AlertManager
from camera_analytics.core.recording_manager import RecordingManager
from camera_analytics.core.vlm_engine import VLMEngine
from camera_analytics.core.event_bus import EventBus, Event, EventType

logger = logging.getLogger(__name__)

# Last VLM description per camera, used to enrich Slack alerts
_last_scene: Dict[str, str] = {}


async def _vlm_describe(vlm_engine, event_bus, alert_manager, frame, cam_id, cam_name, detections, timestamp):
    """Run VLM description in the background without blocking detection."""
    try:
        det_dicts = [d.to_dict() for d in detections]
        scene = await vlm_engine.describe_frame(
            frame, camera_id=cam_id, detections=det_dicts,
        )
        if scene and scene.description:
            logger.info(f"[{cam_id}] Scene: {scene.description[:150]}")
            _last_scene[cam_id] = scene.description

            if event_bus:
                await event_bus.publish(Event(
                    type=EventType.SCENE_DESCRIPTION,
                    camera_id=cam_id,
                    timestamp=timestamp,
                    data={
                        "description": scene.description,
                        "model": scene.model,
                        "detection_count": len(detections),
                    },
                ))

            # Send Slack alert with scene description for person detections
            person_dets = [d for d in detections if d.class_name == "person"]
            if person_dets and alert_manager:
                det_labels = [f"{d.class_name} ({d.confidence:.0%})" for d in detections]
                await alert_manager.send_slack_alert(
                    camera_name=cam_name or cam_id,
                    detections=det_labels,
                    scene_description=scene.description,
                    camera_id=cam_id,
                )
    except Exception as e:
        logger.warning(f"VLM background task failed: {e}")


async def main_pipeline(components: Dict[str, Any]):
    """
    The main processing pipeline.
    """
    camera_manager: CameraManager = components["camera_manager"]
    detection_engine: DetectionEngine = components["detection_engine"]
    tracking_engine: TrackingEngine = components["tracking_engine"]
    analytics_engine: AnalyticsEngine = components["analytics_engine"]
    alert_manager: AlertManager = components["alert_manager"]
    vlm_engine: VLMEngine = components.get("vlm_engine")
    event_bus: EventBus = components.get("event_bus")
    settings = components["settings"]
    fps = settings.default_fps

    # Parse class filter from settings
    class_filter: Optional[List[str]] = None
    if settings.detection_classes.strip():
        class_filter = [c.strip() for c in settings.detection_classes.split(",") if c.strip()]
        logger.info(f"Detection class filter: {class_filter}")
    else:
        logger.info("Detection class filter: ALL classes")

    logger.info("Main pipeline started.")
    frame_count = 0
    vlm_task = None

    while True:
        try:
            # 1. Get frames from all active cameras
            active_cameras = await camera_manager.list_cameras()

            if not active_cameras:
                await asyncio.sleep(2)
                continue

            frames_to_process = []
            camera_ids = []
            camera_names = []
            for cam_id, cam_info in active_cameras.items():
                if cam_info["enabled"] and cam_info["status"] == "connected":
                    frame = await camera_manager.get_frame(cam_id)
                    if frame is not None:
                        frames_to_process.append(frame)
                        camera_ids.append(cam_id)
                        camera_names.append(cam_info.get("name", cam_id))

            if not frames_to_process:
                await asyncio.sleep(1)
                continue

            frame_count += 1
            if frame_count % 50 == 1:
                logger.info(f"Pipeline processing frame {frame_count} from {len(camera_ids)} camera(s)")

            # 2. Run detection per camera
            for i, cam_id in enumerate(camera_ids):
                frame = frames_to_process[i]
                cam_name = camera_names[i]

                # Pass class filter to detection engine
                detections = await detection_engine.detect(frame, classes=class_filter)

                # 3. Update tracks
                tracks = tracking_engine.update(detections)

                # 4. Run analytics
                events = analytics_engine.update(tracks)

                # 5. Publish detection events to event bus
                now = datetime.now(UTC).isoformat()
                if detections and event_bus:
                    await event_bus.publish(Event(
                        type=EventType.DETECTION,
                        camera_id=cam_id,
                        timestamp=now,
                        data={
                            "count": len(detections),
                            "objects": [d.to_dict() for d in detections],
                        },
                    ))

                    if frame_count % 10 == 1:
                        det_summary = ", ".join(f"{d.class_name}({d.confidence:.0%})" for d in detections)
                        logger.info(f"[{cam_id}] Detected: {det_summary}")

                # 6. VLM scene description + Slack alert (fire and forget)
                if detections and vlm_engine and vlm_engine.is_available:
                    if vlm_task is None or vlm_task.done():
                        vlm_task = asyncio.create_task(
                            _vlm_describe(
                                vlm_engine, event_bus, alert_manager,
                                frame.copy(), cam_id, cam_name, detections, now,
                            )
                        )
                elif detections:
                    # No VLM available — send Slack alert with detection info only
                    person_dets = [d for d in detections if d.class_name == "person"]
                    if person_dets:
                        det_labels = [f"{d.class_name} ({d.confidence:.0%})" for d in detections]
                        await alert_manager.send_slack_alert(
                            camera_name=cam_name,
                            detections=det_labels,
                            scene_description=_last_scene.get(cam_id),
                            camera_id=cam_id,
                        )

                # 7. Evaluate alert rules
                for event in events:
                    await alert_manager.evaluate(event.__dict__)

            await asyncio.sleep(1 / fps)

        except asyncio.CancelledError:
            logger.info("Main pipeline cancelled.")
            if vlm_task and not vlm_task.done():
                vlm_task.cancel()
            break
        except Exception as e:
            logger.exception(f"Error in main pipeline: {e}")
            await asyncio.sleep(5)
