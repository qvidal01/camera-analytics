"""
UniFi Protect integration for auto-discovering cameras.

Connects to a UniFi Protect controller (UDM Pro, Cloud Key, etc.)
and retrieves camera info + RTSP stream URLs.
"""

import logging
from dataclasses import dataclass
from typing import List, Optional

import httpx

from camera_analytics.core.camera_manager import CameraConfig, CameraType

logger = logging.getLogger(__name__)


@dataclass
class ProtectCamera:
    """Camera info from UniFi Protect."""

    id: str
    name: str
    type: str  # e.g., "UVC G4 Bullet"
    mac: str
    host: str
    is_connected: bool
    rtsp_url: Optional[str] = None
    snapshot_url: Optional[str] = None
    channel_id: Optional[str] = None


class UniFiProtectClient:
    """
    Client for UniFi Protect controller API.

    Supports UniFi OS (UDM Pro, UDM SE, Cloud Key Gen2+).

    Usage:
        client = UniFiProtectClient("192.168.1.1", "admin", "password")
        cameras = await client.discover_cameras()
        configs = client.to_camera_configs(cameras)
    """

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        port: int = 443,
        verify_ssl: bool = False,
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self._base_url = f"https://{host}:{port}"
        self._client: Optional[httpx.AsyncClient] = None
        self._api_path: Optional[str] = None
        self._csrf_token: Optional[str] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                verify=self.verify_ssl,
                timeout=15.0,
                follow_redirects=True,
            )
        return self._client

    async def authenticate(self) -> bool:
        """Authenticate with the UniFi Protect controller."""
        client = await self._get_client()

        # Try UniFi OS auth first (UDM Pro / UDM SE)
        try:
            resp = await client.post(
                f"{self._base_url}/api/auth/login",
                json={"username": self.username, "password": self.password},
            )
            if resp.status_code == 200:
                self._api_path = "/proxy/protect/api"
                self._csrf_token = resp.headers.get("x-csrf-token")
                logger.info(f"Authenticated with UniFi OS at {self.host}")
                return True
        except httpx.ConnectError:
            pass

        # Fallback: direct Protect API (Cloud Key Gen2)
        try:
            resp = await client.post(
                f"{self._base_url}/api/auth",
                json={"username": self.username, "password": self.password},
            )
            if resp.status_code == 200:
                self._api_path = "/api"
                logger.info(f"Authenticated with Protect directly at {self.host}")
                return True
        except httpx.ConnectError:
            pass

        logger.error(f"Failed to authenticate with UniFi Protect at {self.host}")
        return False

    async def discover_cameras(self) -> List[ProtectCamera]:
        """Discover all cameras from the Protect controller."""
        if self._api_path is None:
            if not await self.authenticate():
                return []

        client = await self._get_client()

        headers = {}
        if self._csrf_token:
            headers["x-csrf-token"] = self._csrf_token

        try:
            resp = await client.get(
                f"{self._base_url}{self._api_path}/cameras",
                headers=headers,
            )
            resp.raise_for_status()
            cameras_data = resp.json()
        except Exception as e:
            logger.error(f"Failed to fetch cameras from Protect: {e}")
            return []

        cameras = []
        for cam in cameras_data:
            # Build RTSP URL from camera channels
            rtsp_url = None
            channel_id = None
            channels = cam.get("channels", [])
            # Prefer the highest quality channel with RTSP enabled
            for channel in sorted(channels, key=lambda c: c.get("width", 0), reverse=True):
                if channel.get("isRtspEnabled"):
                    channel_id = str(channel.get("id", 0))
                    rtsp_alias = channel.get("rtspAlias", "")
                    if rtsp_alias:
                        rtsp_url = f"rtsp://{self.host}:7447/{rtsp_alias}"
                    break

            # If no RTSP alias, try constructing from camera ID
            if not rtsp_url and cam.get("id"):
                rtsp_url = f"rtsp://{self.host}:7447/{cam['id']}"

            snapshot_url = f"{self._base_url}{self._api_path}/cameras/{cam['id']}/snapshot"

            cameras.append(ProtectCamera(
                id=cam.get("id", ""),
                name=cam.get("name", "Unknown"),
                type=cam.get("type", "Unknown"),
                mac=cam.get("mac", ""),
                host=cam.get("host", ""),
                is_connected=cam.get("isConnected", False),
                rtsp_url=rtsp_url,
                snapshot_url=snapshot_url,
                channel_id=channel_id,
            ))

        logger.info(f"Discovered {len(cameras)} cameras from UniFi Protect")
        return cameras

    def to_camera_configs(
        self,
        cameras: List[ProtectCamera],
        fps: int = 15,
        resolution: tuple[int, int] = (1920, 1080),
        only_connected: bool = True,
    ) -> List[CameraConfig]:
        """Convert discovered cameras to CameraConfig objects for the CameraManager."""
        configs = []
        for cam in cameras:
            if only_connected and not cam.is_connected:
                continue
            if not cam.rtsp_url:
                logger.warning(f"Camera {cam.name} has no RTSP URL, skipping")
                continue

            configs.append(CameraConfig(
                id=f"unifi-{cam.id[:12]}",
                name=cam.name,
                source_type=CameraType.RTSP,
                source_url=cam.rtsp_url,
                fps=fps,
                resolution=resolution,
            ))
        return configs

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
