"""
API router for VLM scene descriptions.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional

from camera_analytics.core.camera_manager import CameraManager
from camera_analytics.core.detection_engine import DetectionEngine
from camera_analytics.core.vlm_engine import VLMEngine

router = APIRouter()


class SceneResponse(BaseModel):
    camera_id: str
    description: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    detections_summary: Optional[str] = None


class SceneRequest(BaseModel):
    prompt: Optional[str] = Field(None, description="Custom prompt override")


def get_vlm_engine(request: Request) -> VLMEngine:
    engine = request.app.state.core_components.get("vlm_engine")
    if engine is None or not engine.is_available:
        raise HTTPException(
            status_code=503,
            detail="VLM engine not available. Set VLM_ENABLED=true and configure VLM_API_URL.",
        )
    return engine


def get_camera_manager(request: Request) -> CameraManager:
    return request.app.state.core_components["camera_manager"]


def get_detection_engine(request: Request) -> DetectionEngine:
    return request.app.state.core_components["detection_engine"]


@router.post("/cameras/{camera_id}/describe", response_model=SceneResponse)
async def describe_camera_scene(
    camera_id: str,
    body: Optional[SceneRequest] = None,
    vlm: VLMEngine = Depends(get_vlm_engine),
    camera_manager: CameraManager = Depends(get_camera_manager),
    detection_engine: DetectionEngine = Depends(get_detection_engine),
):
    """Get a VLM scene description for a camera's current frame."""
    frame = await camera_manager.get_frame(camera_id)
    if frame is None:
        raise HTTPException(status_code=404, detail="Camera not found or no frame available.")

    # Run detection first to give VLM context
    detections = await detection_engine.detect(frame)
    det_dicts = [d.to_dict() for d in detections] if detections else None

    custom_prompt = body.prompt if body else None
    scene = await vlm.describe_frame(
        frame,
        camera_id=camera_id,
        detections=det_dicts,
        custom_prompt=custom_prompt,
    )

    if scene is None:
        raise HTTPException(status_code=502, detail="VLM failed to generate description.")

    return SceneResponse(
        camera_id=camera_id,
        description=scene.description,
        model=scene.model,
        prompt_tokens=scene.prompt_tokens,
        completion_tokens=scene.completion_tokens,
        detections_summary=scene.detections_summary,
    )


@router.get("/vlm/status")
async def vlm_status(request: Request):
    """Get VLM engine status."""
    engine = request.app.state.core_components.get("vlm_engine")
    if engine is None:
        return {"enabled": False, "available": False}
    return engine.get_info()
