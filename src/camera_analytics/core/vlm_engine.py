"""
Vision Language Model (VLM) engine for scene understanding.

Provides narrative scene descriptions from camera frames using models like
Qwen3-VL via llama-server or Ollama (OpenAI-compatible API).

Instead of just "person detected", get descriptions like:
"A mailman is delivering mail to a suburban house, wearing a blue uniform
and carrying a white mail bag."
"""

import base64
import logging
from dataclasses import dataclass, field
from typing import List, Optional

import httpx
import numpy as np

logger = logging.getLogger(__name__)

# Default prompt for security camera scene description
DEFAULT_PROMPT = (
    "Describe what is happening in this security camera frame. "
    "Include details about people, vehicles, activities, and anything notable. "
    "Be concise but descriptive. Focus on security-relevant details."
)


@dataclass
class SceneDescription:
    """Result from VLM scene analysis."""

    description: str
    camera_id: Optional[str] = None
    model: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    detections_summary: Optional[str] = None


@dataclass
class VLMConfig:
    """Configuration for the VLM engine."""

    api_url: str = "http://localhost:8080/v1/chat/completions"
    model: str = "qwen3-vl-2b-instruct"
    prompt: str = DEFAULT_PROMPT
    max_tokens: int = 256
    temperature: float = 0.3
    timeout: float = 30.0
    enabled: bool = False


class VLMEngine:
    """
    Vision Language Model engine for scene understanding.

    Connects to any OpenAI-compatible vision API:
    - llama-server serving Qwen3-VL GGUF models
    - Ollama with vision models (llava, qwen2-vl, etc.)
    - Any OpenAI-compatible VLM endpoint

    Usage:
        engine = VLMEngine(VLMConfig(
            api_url="http://192.168.0.234:11434/v1/chat/completions",
            model="qwen3-vl:2b",
            enabled=True,
        ))
        description = await engine.describe_frame(frame)
    """

    def __init__(self, config: VLMConfig):
        self.config = config
        self._client: Optional[httpx.AsyncClient] = None
        self._available = False

    async def initialize(self) -> bool:
        """Initialize the HTTP client and check if the VLM server is reachable."""
        if not self.config.enabled:
            logger.info("VLM engine disabled")
            return False

        self._client = httpx.AsyncClient(timeout=self.config.timeout)

        # Probe the server
        try:
            base_url = self.config.api_url.rsplit("/chat/completions", 1)[0]
            models_url = f"{base_url}/models"
            resp = await self._client.get(models_url)
            if resp.status_code == 200:
                data = resp.json()
                available_models = [m.get("id", "") for m in data.get("data", [])]
                logger.info(f"VLM server reachable. Available models: {available_models}")
                self._available = True
            else:
                logger.warning(f"VLM server returned {resp.status_code}, proceeding anyway")
                self._available = True
        except httpx.ConnectError:
            logger.warning(f"VLM server not reachable at {self.config.api_url}")
            self._available = False
        except Exception as e:
            logger.warning(f"VLM server probe failed: {e}")
            # Still mark available — the /models endpoint may not exist (llama-server)
            self._available = True

        return self._available

    async def shutdown(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    @property
    def is_available(self) -> bool:
        return self.config.enabled and self._available

    def _encode_frame(self, frame: np.ndarray) -> str:
        """Encode a BGR numpy frame to a base64 JPEG string."""
        import cv2

        success, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if not success:
            raise ValueError("Failed to encode frame to JPEG")
        return base64.b64encode(buffer).decode("utf-8")

    def _build_prompt(
        self,
        detections: Optional[List[dict]] = None,
        custom_prompt: Optional[str] = None,
    ) -> str:
        """Build the text prompt, optionally including detection context."""
        prompt = custom_prompt or self.config.prompt

        if detections:
            det_summary = ", ".join(
                f"{d.get('class_name', 'object')} ({d.get('confidence', 0):.0%})"
                for d in detections
            )
            prompt += f"\n\nObjects already detected in this frame: {det_summary}"

        return prompt

    async def describe_frame(
        self,
        frame: np.ndarray,
        camera_id: Optional[str] = None,
        detections: Optional[List[dict]] = None,
        custom_prompt: Optional[str] = None,
    ) -> Optional[SceneDescription]:
        """
        Generate a scene description for a camera frame.

        Args:
            frame: BGR numpy array from OpenCV
            camera_id: Optional camera identifier
            detections: Optional list of detection dicts to provide context
            custom_prompt: Override the default prompt

        Returns:
            SceneDescription or None if VLM is unavailable/fails
        """
        if not self.is_available or self._client is None:
            return None

        if frame is None or frame.size == 0:
            logger.warning("Empty frame provided to VLM")
            return None

        try:
            image_b64 = self._encode_frame(frame)
            prompt_text = self._build_prompt(detections, custom_prompt)

            payload = {
                "model": self.config.model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_b64}",
                                },
                            },
                            {
                                "type": "text",
                                "text": prompt_text,
                            },
                        ],
                    }
                ],
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.temperature,
                "chat_template_kwargs": {"enable_thinking": False},
            }

            resp = await self._client.post(self.config.api_url, json=payload)
            resp.raise_for_status()
            data = resp.json()

            choice = data["choices"][0]
            usage = data.get("usage", {})

            # Extract content, stripping any <think> reasoning tags
            content = choice["message"]["content"] or ""
            import re
            content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()

            # If content is empty but reasoning exists, use reasoning
            if not content and choice["message"].get("reasoning"):
                content = choice["message"]["reasoning"].strip()

            description = SceneDescription(
                description=content,
                camera_id=camera_id,
                model=data.get("model", self.config.model),
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
            )

            if detections:
                description.detections_summary = self._build_prompt(detections).split(
                    "Objects already detected"
                )[-1]

            logger.debug(
                f"VLM description for camera {camera_id}: "
                f"{description.description[:100]}..."
            )
            return description

        except httpx.TimeoutException:
            logger.warning(f"VLM request timed out for camera {camera_id}")
            return None
        except httpx.HTTPStatusError as e:
            logger.warning(f"VLM request failed ({e.response.status_code}): {e.response.text[:200]}")
            return None
        except Exception as e:
            logger.exception(f"VLM description failed for camera {camera_id}: {e}")
            return None

    async def describe_frames_batch(
        self,
        frames: List[np.ndarray],
        camera_ids: Optional[List[str]] = None,
        detections_batch: Optional[List[List[dict]]] = None,
    ) -> List[Optional[SceneDescription]]:
        """
        Describe multiple frames. Sends requests concurrently.

        Args:
            frames: List of BGR numpy arrays
            camera_ids: Optional camera IDs corresponding to each frame
            detections_batch: Optional detections per frame

        Returns:
            List of SceneDescription (or None for failures)
        """
        import asyncio

        if not self.is_available:
            return [None] * len(frames)

        camera_ids = camera_ids or [None] * len(frames)
        detections_batch = detections_batch or [None] * len(frames)

        tasks = [
            self.describe_frame(frame, cam_id, dets)
            for frame, cam_id, dets in zip(frames, camera_ids, detections_batch)
        ]
        return await asyncio.gather(*tasks)

    def get_info(self) -> dict:
        """Get VLM engine status info."""
        return {
            "enabled": self.config.enabled,
            "available": self._available,
            "api_url": self.config.api_url,
            "model": self.config.model,
            "max_tokens": self.config.max_tokens,
        }
