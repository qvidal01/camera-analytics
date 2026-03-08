"""
Central event bus for real-time event distribution.

Collects detection events, scene descriptions, and alerts, then distributes
them to WebSocket subscribers and stores recent history.
"""

import asyncio
import json
import logging
from collections import deque
from dataclasses import dataclass, field, asdict
from datetime import datetime, UTC
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    DETECTION = "detection"
    SCENE_DESCRIPTION = "scene_description"
    ALERT = "alert"
    CAMERA_STATUS = "camera_status"
    LINE_CROSSING = "line_crossing"


@dataclass
class Event:
    """A single event in the system."""

    type: EventType
    camera_id: Optional[str]
    timestamp: str
    data: Dict[str, Any]
    id: str = ""

    def __post_init__(self):
        if not self.id:
            ts = int(datetime.now(UTC).timestamp() * 1000)
            self.id = f"{self.type.value}-{self.camera_id or 'sys'}-{ts}"

    def to_json(self) -> str:
        return json.dumps(asdict(self), default=str)


class EventBus:
    """
    Central event bus with WebSocket broadcasting and history.

    Components publish events here. WebSocket clients subscribe to
    receive them in real time. Recent events are kept in memory
    for the history API.

    Usage:
        bus = EventBus(max_history=500)

        # In pipeline — publish events:
        await bus.publish(Event(
            type=EventType.DETECTION,
            camera_id="front-door",
            timestamp=datetime.now(UTC).isoformat(),
            data={"class_name": "person", "confidence": 0.92},
        ))

        # In WebSocket endpoint — subscribe:
        await bus.subscribe(websocket)
    """

    def __init__(self, max_history: int = 500):
        self._subscribers: Set[WebSocket] = set()
        self._history: deque[Event] = deque(maxlen=max_history)
        self._lock = asyncio.Lock()

    async def publish(self, event: Event):
        """Publish an event to all subscribers and store in history."""
        self._history.append(event)

        # Broadcast to WebSocket subscribers
        if self._subscribers:
            message = event.to_json()
            dead: List[WebSocket] = []

            for ws in self._subscribers:
                try:
                    await ws.send_text(message)
                except Exception:
                    dead.append(ws)

            # Clean up disconnected clients
            for ws in dead:
                self._subscribers.discard(ws)

    async def subscribe(self, websocket: WebSocket):
        """Add a WebSocket client as a subscriber."""
        await websocket.accept()
        self._subscribers.add(websocket)
        logger.info(f"WebSocket client subscribed ({len(self._subscribers)} total)")

        try:
            # Keep connection alive, listen for client messages (ping/filter)
            while True:
                try:
                    msg = await websocket.receive_text()
                    # Could handle filter commands here in the future
                    if msg == "ping":
                        await websocket.send_text('{"type":"pong"}')
                except Exception:
                    break
        finally:
            self._subscribers.discard(websocket)
            logger.info(f"WebSocket client disconnected ({len(self._subscribers)} total)")

    def get_history(
        self,
        limit: int = 50,
        event_type: Optional[EventType] = None,
        camera_id: Optional[str] = None,
    ) -> List[Dict]:
        """Get recent event history with optional filtering."""
        events = list(self._history)
        events.reverse()  # Most recent first

        if event_type:
            events = [e for e in events if e.type == event_type]
        if camera_id:
            events = [e for e in events if e.camera_id == camera_id]

        return [asdict(e) for e in events[:limit]]

    @property
    def subscriber_count(self) -> int:
        return len(self._subscribers)
