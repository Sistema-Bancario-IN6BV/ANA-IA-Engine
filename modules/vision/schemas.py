from __future__ import annotations

from pydantic import BaseModel


class BoundingBox(BaseModel):
    x_min: float
    y_min: float
    x_max: float
    y_max: float


class DetectedObject(BaseModel):
    label: str
    confidence: float
    bbox: BoundingBox
    description: str = ""


class SceneAnalysis(BaseModel):
    objects: list[DetectedObject]
    person_detected: bool
    is_alone: bool
    medication_detected: bool
    fall_risk_detected: bool
    summary: str
