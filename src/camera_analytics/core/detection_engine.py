"""
Object detection engine using YOLO models.

This module provides AI-powered object detection capabilities for identifying
people, vehicles, and other objects in video frames.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
import torch

logger = logging.getLogger(__name__)


@dataclass
class Detection:
    """
    Represents a single object detection.

    Attributes:
        class_name: Object class (e.g., 'person', 'car')
        class_id: Numeric class identifier
        confidence: Detection confidence score (0.0-1.0)
        bbox: Bounding box as (x1, y1, x2, y2) in pixels
        track_id: Optional tracking ID if object is being tracked
    """

    class_name: str
    class_id: int
    confidence: float
    bbox: Tuple[int, int, int, int]
    track_id: Optional[int] = None

    def center(self) -> Tuple[int, int]:
        """
        Calculate center point of bounding box.

        Returns:
            Tuple[int, int]: (center_x, center_y)
        """
        x1, y1, x2, y2 = self.bbox
        return ((x1 + x2) // 2, (y1 + y2) // 2)

    def area(self) -> int:
        """
        Calculate area of bounding box.

        Returns:
            int: Area in square pixels
        """
        x1, y1, x2, y2 = self.bbox
        return (x2 - x1) * (y2 - y1)

    def to_dict(self) -> dict:
        """
        Convert detection to dictionary.

        Returns:
            dict: Detection as dictionary
        """
        return {
            "class_name": self.class_name,
            "class_id": self.class_id,
            "confidence": round(self.confidence, 3),
            "bbox": list(self.bbox),
            "track_id": self.track_id,
            "center": self.center(),
            "area": self.area(),
        }


class DetectionEngine:
    """
    AI-powered object detection engine.

    Uses YOLOv8 models for real-time object detection with GPU acceleration support.
    """

    # COCO class names (80 classes)
    COCO_CLASSES = [
        "person",
        "bicycle",
        "car",
        "motorcycle",
        "airplane",
        "bus",
        "train",
        "truck",
        "boat",
        "traffic light",
        "fire hydrant",
        "stop sign",
        "parking meter",
        "bench",
        "bird",
        "cat",
        "dog",
        "horse",
        "sheep",
        "cow",
        "elephant",
        "bear",
        "zebra",
        "giraffe",
        "backpack",
        "umbrella",
        "handbag",
        "tie",
        "suitcase",
        "frisbee",
        "skis",
        "snowboard",
        "sports ball",
        "kite",
        "baseball bat",
        "baseball glove",
        "skateboard",
        "surfboard",
        "tennis racket",
        "bottle",
        "wine glass",
        "cup",
        "fork",
        "knife",
        "spoon",
        "bowl",
        "banana",
        "apple",
        "sandwich",
        "orange",
        "broccoli",
        "carrot",
        "hot dog",
        "pizza",
        "donut",
        "cake",
        "chair",
        "couch",
        "potted plant",
        "bed",
        "dining table",
        "toilet",
        "tv",
        "laptop",
        "mouse",
        "remote",
        "keyboard",
        "cell phone",
        "microwave",
        "oven",
        "toaster",
        "sink",
        "refrigerator",
        "book",
        "clock",
        "vase",
        "scissors",
        "teddy bear",
        "hair drier",
        "toothbrush",
    ]

    def __init__(
        self,
        model_name: str = "yolov8n",
        device: str = "cpu",
        confidence_threshold: float = 0.5,
        iou_threshold: float = 0.45,
    ):
        """
        Initialize detection engine.

        Args:
            model_name: YOLO model name (yolov8n, yolov8s, yolov8m, yolov8l, yolov8x)
            device: Device for inference ('cpu', 'cuda', 'mps')
            confidence_threshold: Minimum confidence for detections (0.0-1.0)
            iou_threshold: IoU threshold for Non-Maximum Suppression

        Raises:
            ValueError: If parameters are invalid
        """
        if not 0.0 <= confidence_threshold <= 1.0:
            raise ValueError("confidence_threshold must be between 0.0 and 1.0")

        self.model_name = model_name
        self.device = device
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self._model = None
        self._device_type = self._get_device()

        logger.info(
            f"DetectionEngine initialized: model={model_name}, "
            f"device={self._device_type}, conf={confidence_threshold}"
        )

    def _get_device(self) -> str:
        """
        Determine available device for inference.

        Returns:
            str: Device string ('cuda', 'mps', or 'cpu')
        """
        if self.device == "cuda" and torch.cuda.is_available():
            logger.info(f"Using CUDA GPU: {torch.cuda.get_device_name(0)}")
            return "cuda"
        elif self.device == "mps" and torch.backends.mps.is_available():
            logger.info("Using Apple Metal Performance Shaders (MPS)")
            return "mps"
        else:
            if self.device != "cpu":
                logger.warning(f"Requested device '{self.device}' not available, using CPU")
            return "cpu"

    async def load_model(self, model_path: Optional[Path] = None) -> bool:
        """
        Load YOLO model.

        Args:
            model_path: Optional path to model file. If None, downloads from Ultralytics.

        Returns:
            bool: True if model loaded successfully

        Note:
            This is a stub implementation. In production, this would use
            Ultralytics YOLO library to load the actual model.
        """
        try:
            logger.info(f"Loading model: {self.model_name}")

            # Stub: In production, would use:
            # from ultralytics import YOLO
            # self._model = YOLO(model_path or f"{self.model_name}.pt")
            # self._model.to(self._device_type)

            # For now, mark as loaded
            self._model = "stub_model"

            logger.info(f"Model {self.model_name} loaded successfully")
            return True

        except Exception as e:
            logger.exception(f"Error loading model: {e}")
            return False

    async def detect(
        self,
        frame: np.ndarray,
        classes: Optional[List[str]] = None,
    ) -> List[Detection]:
        """
        Detect objects in a frame.

        Args:
            frame: Input frame as numpy array (BGR format)
            classes: Optional list of class names to filter (e.g., ['person', 'car'])

        Returns:
            List[Detection]: List of detected objects

        Raises:
            RuntimeError: If model not loaded
        """
        if self._model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        if frame is None or frame.size == 0:
            logger.warning("Empty frame provided for detection")
            return []

        try:
            # Stub: In production, would run actual inference
            # results = self._model(frame, conf=self.confidence_threshold,
            #                       iou=self.iou_threshold, device=self._device_type)

            # For stub, return empty list
            # In production, would parse results and create Detection objects
            detections: List[Detection] = []

            # Example of how detections would be created:
            # for result in results:
            #     for box in result.boxes:
            #         class_id = int(box.cls[0])
            #         class_name = self.COCO_CLASSES[class_id]
            #
            #         # Filter by requested classes
            #         if classes and class_name not in classes:
            #             continue
            #
            #         detection = Detection(
            #             class_name=class_name,
            #             class_id=class_id,
            #             confidence=float(box.conf[0]),
            #             bbox=tuple(map(int, box.xyxy[0]))
            #         )
            #         detections.append(detection)

            return detections

        except Exception as e:
            logger.exception(f"Error during detection: {e}")
            return []

    async def detect_batch(
        self,
        frames: List[np.ndarray],
        classes: Optional[List[str]] = None,
    ) -> List[List[Detection]]:
        """
        Detect objects in multiple frames (batched for efficiency).

        Args:
            frames: List of input frames
            classes: Optional list of class names to filter

        Returns:
            List[List[Detection]]: List of detection lists (one per frame)

        Note:
            Batching improves GPU utilization and throughput.
        """
        if self._model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        try:
            # Stub: In production, would run batched inference
            # results = self._model(frames, conf=self.confidence_threshold,
            #                       iou=self.iou_threshold, device=self._device_type)

            # For stub, return empty lists
            return [[] for _ in frames]

        except Exception as e:
            logger.exception(f"Error during batch detection: {e}")
            return [[] for _ in frames]

    def get_supported_classes(self) -> List[str]:
        """
        Get list of supported object classes.

        Returns:
            List[str]: List of class names
        """
        return self.COCO_CLASSES.copy()

    async def optimize_model(
        self,
        export_format: str = "onnx",
        quantize: bool = False,
    ) -> bool:
        """
        Optimize model for faster inference.

        Args:
            export_format: Format to export ('onnx', 'tensorrt', 'openvino')
            quantize: Whether to apply quantization

        Returns:
            bool: True if optimization successful

        Note:
            ONNX export improves inference speed.
            TensorRT provides best performance on NVIDIA GPUs.
            Quantization reduces model size with minimal accuracy loss.
        """
        try:
            logger.info(f"Optimizing model to {export_format} format (quantize={quantize})")

            # Stub: In production would export model:
            # self._model.export(format=export_format, quantize=quantize)

            logger.info("Model optimization complete")
            return True

        except Exception as e:
            logger.exception(f"Error optimizing model: {e}")
            return False

    def get_model_info(self) -> dict:
        """
        Get model information and statistics.

        Returns:
            dict: Model metadata
        """
        return {
            "model_name": self.model_name,
            "device": self._device_type,
            "confidence_threshold": self.confidence_threshold,
            "iou_threshold": self.iou_threshold,
            "num_classes": len(self.COCO_CLASSES),
            "loaded": self._model is not None,
        }
