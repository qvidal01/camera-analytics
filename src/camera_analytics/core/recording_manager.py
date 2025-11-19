"""Recording manager for saving video clips."""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class RecordingManager:
    """Manages video recording and storage."""

    def __init__(self, storage_path: Path):
        """Initialize recording manager."""
        self.storage_path = storage_path
        logger.info(f"RecordingManager initialized: {storage_path}")
