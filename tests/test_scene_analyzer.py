import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modules.vision.schemas import BoundingBox, DetectedObject
from modules.vision.scene_analyzer import SceneAnalyzer

_BOX = BoundingBox(x_min=0, y_min=0, x_max=1, y_max=1)


def make_object(label, confidence=0.9):
    return DetectedObject(label=label, confidence=confidence, bbox=_BOX, description=label)


def test_no_objects_means_no_person_detected():
    result = SceneAnalyzer._interpret([])

    assert result.person_detected is False
    assert result.is_alone is False
    assert "No se detectó a la persona" in result.summary


def test_single_person_is_alone():
    result = SceneAnalyzer._interpret([make_object("person")])

    assert result.person_detected is True
    assert result.is_alone is True


def test_two_people_not_alone():
    result = SceneAnalyzer._interpret([make_object("person"), make_object("person")])

    assert result.person_detected is True
    assert result.is_alone is False


def test_bottle_triggers_medication_flag():
    result = SceneAnalyzer._interpret([make_object("person"), make_object("bottle")])

    assert result.medication_detected is True
    assert result.fall_risk_detected is False


def test_backpack_on_floor_triggers_fall_risk_flag():
    result = SceneAnalyzer._interpret([make_object("person"), make_object("backpack")])

    assert result.fall_risk_detected is True


def test_unrelated_objects_do_not_trigger_dead_labels():
    # Regression guard: "stairs"/"carpet"/"man"/"woman" are not real COCO labels
    # the model ever emits — this proves the flags stay off when only
    # irrelevant/impossible-looking labels are present.
    result = SceneAnalyzer._interpret([make_object("chair"), make_object("tv")])

    assert result.medication_detected is False
    assert result.fall_risk_detected is False
