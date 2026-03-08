"""
API router for camera discovery (UniFi Protect + ONVIF).
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from camera_analytics.core.camera_manager import CameraManager
from camera_analytics.core.unifi_protect import UniFiProtectClient, ProtectCamera
from camera_analytics.core.onvif_discovery import ONVIFDiscovery, ONVIFDevice

router = APIRouter()


# --- Request/Response models ---

class UniFiProtectRequest(BaseModel):
    host: str = Field(..., description="UniFi Protect controller IP/hostname")
    username: str = Field(..., description="Admin username")
    password: str = Field(..., description="Admin password")
    port: int = Field(443, description="Controller port")
    verify_ssl: bool = Field(False, description="Verify SSL certificate")


class ONVIFRequest(BaseModel):
    username: str = Field("admin", description="Camera username")
    password: str = Field("", description="Camera password")
    timeout: float = Field(5.0, ge=1.0, le=30.0, description="Discovery timeout in seconds")


class DiscoveredCamera(BaseModel):
    id: str
    name: str
    source: str  # "unifi_protect" or "onvif"
    address: str
    rtsp_url: Optional[str] = None
    model: Optional[str] = None
    connected: bool = True


class AddDiscoveredRequest(BaseModel):
    camera_ids: List[str] = Field(..., description="IDs of discovered cameras to add")
    fps: int = Field(15, ge=1, le=60)
    resolution: List[int] = Field([1920, 1080])


# --- In-memory store for last discovery results ---
_last_discovery: dict = {"unifi": [], "onvif": [], "configs": {}}


def get_camera_manager(request: Request) -> CameraManager:
    return request.app.state.core_components["camera_manager"]


# --- UniFi Protect ---

@router.post("/discovery/unifi-protect", response_model=List[DiscoveredCamera])
async def discover_unifi_protect(body: UniFiProtectRequest):
    """Discover cameras from a UniFi Protect controller."""
    client = UniFiProtectClient(
        host=body.host,
        username=body.username,
        password=body.password,
        port=body.port,
        verify_ssl=body.verify_ssl,
    )

    try:
        authenticated = await client.authenticate()
        if not authenticated:
            raise HTTPException(status_code=401, detail="Failed to authenticate with UniFi Protect")

        cameras = await client.discover_cameras()
        configs = client.to_camera_configs(cameras)

        # Store results for later add
        result = []
        _last_discovery["unifi"] = cameras
        for cam, cfg in zip(cameras, configs):
            _last_discovery["configs"][cfg.id] = cfg
            result.append(DiscoveredCamera(
                id=cfg.id,
                name=cam.name,
                source="unifi_protect",
                address=cam.host or body.host,
                rtsp_url=cam.rtsp_url,
                model=cam.type,
                connected=cam.is_connected,
            ))

        # Include cameras without RTSP (for visibility)
        added_ids = {c.id for c in configs}
        for cam in cameras:
            temp_id = f"unifi-{cam.id[:12]}"
            if temp_id not in added_ids:
                result.append(DiscoveredCamera(
                    id=temp_id,
                    name=cam.name,
                    source="unifi_protect",
                    address=cam.host or body.host,
                    rtsp_url=None,
                    model=cam.type,
                    connected=cam.is_connected,
                ))

        return result

    finally:
        await client.close()


# --- ONVIF ---

@router.post("/discovery/onvif", response_model=List[DiscoveredCamera])
async def discover_onvif(body: ONVIFRequest):
    """Discover ONVIF cameras on the local network."""
    discovery = ONVIFDiscovery()

    try:
        devices = await discovery.discover_with_streams(
            username=body.username,
            password=body.password,
            timeout=body.timeout,
        )

        configs = discovery.to_camera_configs(devices)

        result = []
        _last_discovery["onvif"] = devices
        for device, cfg in zip(devices, configs):
            _last_discovery["configs"][cfg.id] = cfg
            result.append(DiscoveredCamera(
                id=cfg.id,
                name=device.name,
                source="onvif",
                address=device.address,
                rtsp_url=device.rtsp_url,
                model=f"{device.manufacturer} {device.model}",
                connected=True,
            ))

        # Include devices without RTSP
        added_addrs = {d.address for d in devices if d.rtsp_url}
        for device in devices:
            if device.address not in added_addrs:
                result.append(DiscoveredCamera(
                    id=f"onvif-{device.address.replace('.', '-')}",
                    name=device.name,
                    source="onvif",
                    address=device.address,
                    rtsp_url=None,
                    model=f"{device.manufacturer} {device.model}",
                    connected=True,
                ))

        return result

    finally:
        await discovery.close()


# --- Add discovered cameras ---

@router.post("/discovery/add", status_code=201)
async def add_discovered_cameras(
    body: AddDiscoveredRequest,
    camera_manager: CameraManager = Depends(get_camera_manager),
):
    """Add previously discovered cameras to the system."""
    added = []
    failed = []

    for cam_id in body.camera_ids:
        config = _last_discovery["configs"].get(cam_id)
        if config is None:
            failed.append({"id": cam_id, "error": "Not found in discovery results. Run discovery first."})
            continue

        config.fps = body.fps
        config.resolution = tuple(body.resolution)

        try:
            success = await camera_manager.add_camera(config)
            if success:
                added.append(cam_id)
            else:
                failed.append({"id": cam_id, "error": "Failed to connect"})
        except ValueError as e:
            failed.append({"id": cam_id, "error": str(e)})

    return {"added": added, "failed": failed}
