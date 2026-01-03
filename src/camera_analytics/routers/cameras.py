"""
API router for camera management.
"""


from fastapi import APIRouter, Depends, HTTPException, Request

from camera_analytics.core.camera_manager import CameraConfig, CameraManager, CameraStatus

router = APIRouter()


def get_camera_manager(request: Request) -> CameraManager:
    """Dependency to get the CameraManager instance."""
    return request.app.state.core_components["camera_manager"]


@router.get("/cameras", response_model=list[dict])
async def list_cameras(camera_manager: CameraManager = Depends(get_camera_manager)):
    """List all cameras."""
    return await camera_manager.list_cameras()


@router.post("/cameras", status_code=201)
async def add_camera(
    config: CameraConfig,
    camera_manager: CameraManager = Depends(get_camera_manager),
):
    """Add a new camera."""
    try:
        success = await camera_manager.add_camera(config)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to connect to camera.")
        return {"message": "Camera added successfully."}
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.delete("/cameras/{camera_id}", status_code=204)
async def remove_camera(
    camera_id: str,
    camera_manager: CameraManager = Depends(get_camera_manager),
):
    """Remove a camera."""
    await camera_manager.remove_camera(camera_id)
    return


@router.get("/cameras/{camera_id}/status", response_model=CameraStatus)
async def get_camera_status(
    camera_id: str,
    camera_manager: CameraManager = Depends(get_camera_manager),
):
    """Get the status of a camera."""
    status = await camera_manager.get_camera_status(camera_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Camera not found.")
    return status
