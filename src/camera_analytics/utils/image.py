"""Image processing utilities."""

import logging

logger = logging.getLogger(__name__)


class ImageProcessor:
    """Utility functions for image processing."""

    @staticmethod
    def normalize(image):
        """Normalize image to 0-1 range."""
        return image / 255.0
