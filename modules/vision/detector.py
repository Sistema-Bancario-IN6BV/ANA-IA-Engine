from __future__ import annotations

import logging
from functools import lru_cache
from typing import Optional

import PIL.Image

from core.config import settings
from core.exceptions import VisionInferenceError
from modules.vision.schemas import BoundingBox, DetectedObject

logger = logging.getLogger(__name__)

_LABEL_DESCRIPTIONS: dict[str, str] = {
    "person": "persona",
    "chair": "silla",
    "couch": "sofá",
    "bed": "cama",
    "bottle": "botella",
    "cup": "taza o vaso",
    "wine glass": "copa",
    "knife": "cuchillo",
    "suitcase": "maleta",
    "backpack": "mochila",
    "handbag": "bolso",
    "skateboard": "patineta",
    "dog": "perro",
    "cat": "gato",
    "tv": "televisión",
    "remote": "control remoto",
    "book": "libro",
    "clock": "reloj",
    "cell phone": "teléfono",
}


@lru_cache(maxsize=1)
def _load_pipeline():
    """Loads the object detection pipeline once (singleton).

    Uses CPU by default; set vision_device="cuda" for GPU acceleration.
    """
    from transformers import pipeline as hf_pipeline

    device = -1 if settings.vision_device == "cpu" else 0
    return hf_pipeline(
        "object-detection",
        model=settings.vision_model_name,
        device=device,
    )


class ObjectDetector:
    """Detects objects in images using a HuggingFace DETR model.

    Covers object detection for elderly environment analysis (H4).
    """

    def __init__(self, confidence_threshold: Optional[float] = None) -> None:
        self._threshold = confidence_threshold or settings.vision_confidence_threshold

    def detect(self, image: PIL.Image.Image) -> list[DetectedObject]:
        """Detects objects in the provided image.

        Args:
            image: PIL image to analyze (RGB recommended).

        Returns:
            List of DetectedObject with confidence >= threshold.

        Raises:
            VisionInferenceError: If the model fails during inference.
        """
        try:
            detector = _load_pipeline()
            raw_results = detector(image)
        except Exception as exc:
            raise VisionInferenceError(f"Object detection failed: {exc}") from exc

        return [
            DetectedObject(
                label=r["label"],
                confidence=round(r["score"], 4),
                bbox=BoundingBox(
                    x_min=r["box"]["xmin"],
                    y_min=r["box"]["ymin"],
                    x_max=r["box"]["xmax"],
                    y_max=r["box"]["ymax"],
                ),
                description=_LABEL_DESCRIPTIONS.get(r["label"].lower(), r["label"]),
            )
            for r in raw_results
            if r["score"] >= self._threshold
        ]
