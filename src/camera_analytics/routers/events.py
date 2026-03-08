"""
API router for the real-time event feed (WebSocket + REST history).
"""

from typing import Optional
from fastapi import APIRouter, Query, Request, WebSocket

from camera_analytics.core.event_bus import EventBus, EventType

router = APIRouter()


def get_event_bus(request: Request) -> EventBus:
    return request.app.state.core_components["event_bus"]


@router.websocket("/ws/events")
async def event_feed(websocket: WebSocket):
    """
    WebSocket endpoint for real-time events.

    Connect to receive live detections, scene descriptions, alerts,
    and camera status changes as they happen.

    Messages are JSON with structure:
        {
            "id": "detection-front-door-1709812345000",
            "type": "detection",
            "camera_id": "front-door",
            "timestamp": "2026-03-07T12:00:00Z",
            "data": { ... }
        }

    Send "ping" to receive a "pong" keepalive.
    """
    event_bus: EventBus = websocket.app.state.core_components["event_bus"]
    await event_bus.subscribe(websocket)


@router.get("/events")
async def get_event_history(
    request: Request,
    limit: int = Query(50, ge=1, le=500),
    type: Optional[str] = Query(None, description="Filter by event type"),
    camera_id: Optional[str] = Query(None, description="Filter by camera ID"),
):
    """
    Get recent event history.

    Returns the most recent events with optional filtering by type and camera.
    """
    event_bus = get_event_bus(request)

    event_type = None
    if type:
        try:
            event_type = EventType(type)
        except ValueError:
            valid = [e.value for e in EventType]
            return {"error": f"Invalid event type. Valid types: {valid}"}

    return event_bus.get_history(
        limit=limit,
        event_type=event_type,
        camera_id=camera_id,
    )


@router.get("/events/status")
async def event_feed_status(request: Request):
    """Get event feed status (subscriber count, history size)."""
    event_bus = get_event_bus(request)
    return {
        "websocket_subscribers": event_bus.subscriber_count,
        "history_size": len(event_bus._history),
    }
