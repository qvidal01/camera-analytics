"""
ONVIF camera discovery and stream URL retrieval.

Discovers ONVIF-compatible IP cameras on the local network using
WS-Discovery, then retrieves RTSP stream URIs from each device.

Works with most IP cameras: Hikvision, Dahua, Amcrest, Reolink,
Axis, Hanwha, Vivotek, etc.
"""

import asyncio
import logging
import re
from dataclasses import dataclass
from typing import List, Optional
from xml.etree import ElementTree

import httpx

from camera_analytics.core.camera_manager import CameraConfig, CameraType

logger = logging.getLogger(__name__)

# WS-Discovery probe message for ONVIF devices
WS_DISCOVERY_PROBE = """<?xml version="1.0" encoding="UTF-8"?>
<e:Envelope xmlns:e="http://www.w3.org/2003/05/soap-envelope"
            xmlns:w="http://schemas.xmlsoap.org/ws/2004/08/addressing"
            xmlns:d="http://schemas.xmlsoap.org/ws/2005/04/discovery"
            xmlns:dn="http://www.onvif.org/ver10/network/wsdl">
  <e:Header>
    <w:MessageID>uuid:NetworkVideoTransmitter</w:MessageID>
    <w:To>urn:schemas-xmlsoap-org:ws:2005:04:discovery</w:To>
    <w:Action>http://schemas.xmlsoap.org/ws/2005/04/discovery/Probe</w:Action>
  </e:Header>
  <e:Body>
    <d:Probe>
      <d:Types>dn:NetworkVideoTransmitter</d:Types>
    </d:Probe>
  </e:Body>
</e:Envelope>"""

# ONVIF GetStreamUri SOAP request
GET_STREAM_URI_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<e:Envelope xmlns:e="http://www.w3.org/2003/05/soap-envelope"
            xmlns:trt="http://www.onvif.org/ver10/media/wsdl"
            xmlns:tt="http://www.onvif.org/ver10/schema">
  <e:Header>
    {security_header}
  </e:Header>
  <e:Body>
    <trt:GetStreamUri>
      <trt:StreamSetup>
        <tt:Stream>RTP-Unicast</tt:Stream>
        <tt:Transport><tt:Protocol>RTSP</tt:Protocol></tt:Transport>
      </trt:StreamSetup>
      <trt:ProfileToken>{profile_token}</trt:ProfileToken>
    </trt:GetStreamUri>
  </e:Body>
</e:Envelope>"""

# ONVIF GetProfiles SOAP request
GET_PROFILES_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<e:Envelope xmlns:e="http://www.w3.org/2003/05/soap-envelope"
            xmlns:trt="http://www.onvif.org/ver10/media/wsdl">
  <e:Header>
    {security_header}
  </e:Header>
  <e:Body>
    <trt:GetProfiles/>
  </e:Body>
</e:Envelope>"""

WS_DISCOVERY_MULTICAST = ("239.255.255.250", 3702)


@dataclass
class ONVIFDevice:
    """A discovered ONVIF device."""

    address: str  # IP address or hostname
    port: int
    name: str
    manufacturer: str
    model: str
    xaddrs: str  # ONVIF service URL
    rtsp_url: Optional[str] = None


class ONVIFDiscovery:
    """
    Discovers ONVIF cameras on the local network.

    Usage:
        discovery = ONVIFDiscovery()
        devices = await discovery.discover(timeout=5)
        # With credentials, get RTSP URLs:
        devices = await discovery.discover_with_streams("admin", "password")
        configs = discovery.to_camera_configs(devices)
    """

    def __init__(self):
        self._http_client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(verify=False, timeout=10.0)
        return self._http_client

    async def discover(self, timeout: float = 5.0) -> List[ONVIFDevice]:
        """
        Discover ONVIF devices on the local network using WS-Discovery.

        Args:
            timeout: How long to listen for responses (seconds)

        Returns:
            List of discovered ONVIF devices
        """
        loop = asyncio.get_event_loop()
        devices: List[ONVIFDevice] = []
        seen_addresses: set = set()

        transport = None
        try:
            # Create UDP socket for WS-Discovery
            transport, protocol = await loop.create_datagram_endpoint(
                lambda: _DiscoveryProtocol(),
                family=2,  # AF_INET
            )

            # Send probe
            transport.sendto(
                WS_DISCOVERY_PROBE.encode("utf-8"),
                WS_DISCOVERY_MULTICAST,
            )

            # Wait for responses
            await asyncio.sleep(timeout)

            # Parse responses
            for data, addr in protocol.responses:
                ip = addr[0]
                if ip in seen_addresses:
                    continue
                seen_addresses.add(ip)

                device = self._parse_probe_response(data, ip)
                if device:
                    devices.append(device)

        except Exception as e:
            logger.error(f"ONVIF discovery failed: {e}")
        finally:
            if transport:
                transport.close()

        logger.info(f"ONVIF discovery found {len(devices)} devices")
        return devices

    def _parse_probe_response(self, data: bytes, fallback_ip: str) -> Optional[ONVIFDevice]:
        """Parse a WS-Discovery probe response."""
        try:
            text = data.decode("utf-8", errors="ignore")
            root = ElementTree.fromstring(text)

            # Extract XAddrs (ONVIF service URL)
            xaddrs = ""
            for elem in root.iter():
                if "XAddrs" in elem.tag and elem.text:
                    xaddrs = elem.text.split()[0]  # Take first URL
                    break

            if not xaddrs:
                return None

            # Extract address from XAddrs
            match = re.search(r"https?://([^:/]+)", xaddrs)
            address = match.group(1) if match else fallback_ip

            port_match = re.search(r":(\d+)", xaddrs)
            port = int(port_match.group(1)) if port_match else 80

            # Extract scopes for device info
            name = address
            manufacturer = "Unknown"
            model = "Unknown"

            for elem in root.iter():
                if "Scopes" in elem.tag and elem.text:
                    scopes = elem.text.split()
                    for scope in scopes:
                        if "/name/" in scope.lower():
                            name = scope.split("/")[-1]
                        elif "/hardware/" in scope.lower():
                            model = scope.split("/")[-1]
                        elif "/mfr/" in scope.lower() or "/manufacturer/" in scope.lower():
                            manufacturer = scope.split("/")[-1]

            return ONVIFDevice(
                address=address,
                port=port,
                name=name.replace("%20", " "),
                manufacturer=manufacturer.replace("%20", " "),
                model=model.replace("%20", " "),
                xaddrs=xaddrs,
            )

        except Exception as e:
            logger.debug(f"Failed to parse ONVIF response from {fallback_ip}: {e}")
            return None

    async def get_rtsp_url(
        self,
        device: ONVIFDevice,
        username: str = "admin",
        password: str = "",
    ) -> Optional[str]:
        """
        Get the RTSP stream URL from an ONVIF device.

        Args:
            device: The ONVIF device
            username: Camera username
            password: Camera password

        Returns:
            RTSP URL or None
        """
        client = await self._get_client()

        security_header = self._build_security_header(username, password)

        # Step 1: Get media profiles
        profiles_xml = GET_PROFILES_TEMPLATE.format(security_header=security_header)

        try:
            media_url = device.xaddrs.replace("/onvif/device_service", "/onvif/media_service")
            if media_url == device.xaddrs:
                media_url = device.xaddrs.rstrip("/") + "/media"

            resp = await client.post(
                media_url,
                content=profiles_xml,
                headers={"Content-Type": "application/soap+xml; charset=utf-8"},
            )

            if resp.status_code != 200:
                # Try the device service URL directly
                resp = await client.post(
                    device.xaddrs,
                    content=profiles_xml,
                    headers={"Content-Type": "application/soap+xml; charset=utf-8"},
                )

            profile_token = self._extract_profile_token(resp.text)
            if not profile_token:
                logger.warning(f"No media profile found for {device.name}")
                return None

            # Step 2: Get stream URI
            stream_xml = GET_STREAM_URI_TEMPLATE.format(
                security_header=security_header,
                profile_token=profile_token,
            )

            resp = await client.post(
                media_url,
                content=stream_xml,
                headers={"Content-Type": "application/soap+xml; charset=utf-8"},
            )

            rtsp_url = self._extract_stream_uri(resp.text)
            if rtsp_url:
                # Inject credentials into RTSP URL if not present
                if username and "@" not in rtsp_url:
                    rtsp_url = rtsp_url.replace("rtsp://", f"rtsp://{username}:{password}@")
                device.rtsp_url = rtsp_url
                return rtsp_url

        except Exception as e:
            logger.warning(f"Failed to get RTSP URL from {device.name} ({device.address}): {e}")

        return None

    def _build_security_header(self, username: str, password: str) -> str:
        """Build a WS-Security header for ONVIF authentication."""
        if not username:
            return ""
        return f"""<Security xmlns="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd">
      <UsernameToken>
        <Username>{username}</Username>
        <Password Type="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-username-token-profile-1.0#PasswordText">{password}</Password>
      </UsernameToken>
    </Security>"""

    def _extract_profile_token(self, xml_text: str) -> Optional[str]:
        """Extract the first media profile token from GetProfiles response."""
        try:
            # Use regex for resilient parsing across namespace variations
            match = re.search(r'token=["\']([^"\']+)["\']', xml_text)
            if match:
                return match.group(1)
        except Exception:
            pass
        return None

    def _extract_stream_uri(self, xml_text: str) -> Optional[str]:
        """Extract RTSP URI from GetStreamUri response."""
        try:
            match = re.search(r"<[^>]*Uri[^>]*>(rtsp://[^<]+)</", xml_text)
            if match:
                return match.group(1)
        except Exception:
            pass
        return None

    async def discover_with_streams(
        self,
        username: str = "admin",
        password: str = "",
        timeout: float = 5.0,
    ) -> List[ONVIFDevice]:
        """Discover devices and retrieve their RTSP stream URLs."""
        devices = await self.discover(timeout)

        for device in devices:
            await self.get_rtsp_url(device, username, password)

        return devices

    def to_camera_configs(
        self,
        devices: List[ONVIFDevice],
        fps: int = 15,
        resolution: tuple[int, int] = (1920, 1080),
    ) -> List[CameraConfig]:
        """Convert discovered ONVIF devices to CameraConfig objects."""
        configs = []
        for device in devices:
            if not device.rtsp_url:
                continue

            safe_id = re.sub(r"[^a-zA-Z0-9-]", "-", device.address)
            configs.append(CameraConfig(
                id=f"onvif-{safe_id}",
                name=f"{device.manufacturer} {device.model} ({device.address})",
                source_type=CameraType.RTSP,
                source_url=device.rtsp_url,
                fps=fps,
                resolution=resolution,
            ))
        return configs

    async def close(self):
        """Close the HTTP client."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None


class _DiscoveryProtocol(asyncio.DatagramProtocol):
    """UDP protocol for collecting WS-Discovery responses."""

    def __init__(self):
        self.responses: List[tuple] = []

    def datagram_received(self, data: bytes, addr: tuple):
        self.responses.append((data, addr))

    def error_received(self, exc: Exception):
        logger.debug(f"Discovery protocol error: {exc}")
