from __future__ import annotations

import PIL.Image

from modules.vision.detector import ObjectDetector
from modules.vision.schemas import DetectedObject, SceneAnalysis

# Label sets must match the actual output vocabulary of the detection model
# (facebook/detr-resnet-50, trained on COCO). COCO has no "stairs"/"carpet"/"rug"
# classes, so those can never be detected — using items commonly left on the
# floor as a trip-hazard proxy instead. Similarly COCO only has "person" (no
# "man"/"woman"), and "cell phone" (not "phone").
_MEDICATION_LABELS: frozenset[str] = frozenset({"bottle", "cup"})
_FALL_RISK_LABELS: frozenset[str] = frozenset({"suitcase", "backpack", "handbag", "skateboard"})
_PERSON_LABEL: str = "person"


class SceneAnalyzer:
    """Interprets detected objects in the context of elderly person safety.

    Covers H4 (detecting relevant environmental changes for early intervention).

    Detects:
    - Whether a person was seen at all, and whether they appear to be alone
    - Presence of medication-adjacent objects (bottles, cups)
    - Objects left on the floor that could be a trip hazard
    """

    def __init__(self) -> None:
        self._detector = ObjectDetector()

    def analyze_scene(self, image: PIL.Image.Image) -> SceneAnalysis:
        """Analyzes an image and returns a safety-focused elderly-context report.

        Args:
            image: PIL image (RGB) to analyze.

        Returns:
            SceneAnalysis with safety flags and a Spanish-language summary.
        """
        objects = self._detector.detect(image)
        return self._interpret(objects)

    @staticmethod
    def _interpret(objects: list[DetectedObject]) -> SceneAnalysis:
        """Pure interpretation step, kept separate from detection so it can be
        unit-tested without loading the underlying detection model."""
        labels = {obj.label.lower() for obj in objects}

        persons = sum(1 for obj in objects if obj.label.lower() == _PERSON_LABEL)
        person_detected = persons >= 1
        is_alone = persons == 1
        medication_detected = bool(labels & _MEDICATION_LABELS)
        fall_risk_detected = bool(labels & _FALL_RISK_LABELS)

        summary_parts: list[str] = []
        if not person_detected:
            summary_parts.append("No se detectó a la persona en la imagen.")
        elif is_alone:
            summary_parts.append("La persona parece estar sola.")
        else:
            summary_parts.append("Hay más de una persona presente.")

        if medication_detected:
            summary_parts.append("Se detectan objetos que podrían ser medicamentos.")
        if fall_risk_detected:
            summary_parts.append(
                "Se detectan objetos en el suelo que podrían representar un riesgo de tropiezo."
            )
        if not medication_detected and not fall_risk_detected:
            summary_parts.append("No se detectan riesgos adicionales en el entorno.")

        return SceneAnalysis(
            objects=objects,
            person_detected=person_detected,
            is_alone=is_alone,
            medication_detected=medication_detected,
            fall_risk_detected=fall_risk_detected,
            summary=" ".join(summary_parts),
        )
