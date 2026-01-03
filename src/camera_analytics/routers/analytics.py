"""
API router for analytics management.
"""


from fastapi import APIRouter, Depends, HTTPException, Request

from camera_analytics.core.analytics_engine import AnalyticsEngine, Line, LineCrossingEvent

router = APIRouter()


def get_analytics_engine(request: Request) -> AnalyticsEngine:
    """Dependency to get the AnalyticsEngine instance."""
    return request.app.state.core_components["analytics_engine"]


@router.post("/analytics/lines", status_code=201)
async def add_line(
    line: Line,
    analytics_engine: AnalyticsEngine = Depends(get_analytics_engine),
):
    """Add a new line for line-crossing detection."""
    try:
        analytics_engine.add_line(line)
        return {"message": "Line added successfully."}
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.delete("/analytics/lines/{line_id}", status_code=204)
async def remove_line(
    line_id: str,
    analytics_engine: AnalyticsEngine = Depends(get_analytics_engine),
):
    """Remove a line."""
    analytics_engine.remove_line(line_id)
    return


@router.get("/analytics/lines", response_model=list[Line])
async def list_lines(analytics_engine: AnalyticsEngine = Depends(get_analytics_engine)):
    """List all defined lines."""
    return list(analytics_engine._lines.values())


@router.get("/analytics/events", response_model=list[LineCrossingEvent])
async def get_latest_events(analytics_engine: AnalyticsEngine = Depends(get_analytics_engine)):
    """Get the latest analytics events."""
    return analytics_engine.get_latest_events()
