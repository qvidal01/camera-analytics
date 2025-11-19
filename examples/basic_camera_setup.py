#!/usr/bin/env python3
"""
Basic Camera Setup Example.

This example demonstrates:
1. Initializing the camera manager
2. Adding a camera (USB webcam)
3. Reading frames from the camera
4. Basic error handling
"""

import asyncio
import logging

from camera_analytics.config import get_settings
from camera_analytics.core.camera_manager import CameraConfig, CameraManager, CameraType
from camera_analytics.utils.logging import setup_logging

# Configure logging
setup_logging(level="INFO")
logger = logging.getLogger(__name__)


async def main():
    """Run the example."""
    logger.info("=== Camera Analytics - Basic Camera Setup ===")

    # Initialize camera manager
    manager = CameraManager()

    # Configure a USB webcam (device 0)
    camera_config = CameraConfig(
        id="webcam-0",
        name="My Webcam",
        source_type=CameraType.USB,
        source_url="/dev/video0",  # Linux: /dev/video0, Windows: 0
        fps=15,
        resolution=(640, 480),
    )

    # Add camera
    logger.info(f"Adding camera: {camera_config.name}")
    success = await manager.add_camera(camera_config)

    if success:
        logger.info("✓ Camera added successfully!")

        # Check camera status
        status = await manager.get_camera_status(camera_config.id)
        logger.info(f"Camera status: {status.value}")

        # Read a few frames
        logger.info("Reading 5 frames from camera...")
        for i in range(5):
            frame = await manager.get_frame(camera_config.id)
            if frame is not None:
                logger.info(f"  Frame {i+1}: shape={frame.shape}")
            else:
                logger.warning(f"  Frame {i+1}: Failed to read")

            await asyncio.sleep(0.1)

        # List all cameras
        cameras = await manager.list_cameras()
        logger.info(f"Total cameras: {len(cameras)}")

        # Cleanup
        await manager.remove_camera(camera_config.id)
        logger.info("✓ Camera removed")

    else:
        logger.error("✗ Failed to add camera")
        logger.info("Make sure you have a webcam connected or use a video file instead")

    # Shutdown manager
    await manager.shutdown()
    logger.info("Done!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.exception(f"Error: {e}")
