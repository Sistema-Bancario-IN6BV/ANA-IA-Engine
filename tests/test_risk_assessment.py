import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.risk_assessment import RiskAssessmentEngine


def make_engine():
    return RiskAssessmentEngine()


def test_empty_text_returns_bajo_risk():
    engine = make_engine()
    result = engine.assess_risk(text="", emotional_state="neutral")

    assert result["risk_level"] == "bajo"
    assert result["overall_score"] == 0.0
    assert result["requires_escalation"] is False


def test_neutral_text_scores_low_risk():
    engine = make_engine()
    result = engine.assess_risk(
        text="Hoy fui a caminar al parque y comí una manzana",
        emotional_state="neutral",
    )

    assert result["risk_level"] == "bajo"
    assert result["alert_threshold_exceeded"] is False


def test_suicidal_language_triggers_critical_escalation():
    engine = make_engine()
    result = engine.assess_risk(
        text="Ya no puedo seguir, quiero morir y mejor muerto que seguir así",
        emotional_state="deprimido",
    )

    assert result["risk_level"] in ("alto", "critico")
    assert result["requires_escalation"] is True
    assert result["dimensions"]["suicidalidad"]["score"] > 0.5


def test_elderly_profile_boosts_suicidality_dimension():
    engine = make_engine()
    text = "quiero morir, ya no puedo seguir"

    baseline = engine.assess_risk(text=text, emotional_state="deprimido")
    with_profile = engine.assess_risk(
        text=text, emotional_state="deprimido", user_profile={"age": 70}
    )

    assert (
        with_profile["dimensions"]["suicidalidad"]["score"]
        >= baseline["dimensions"]["suicidalidad"]["score"]
    )


def test_ascending_history_trend_increases_score():
    engine = make_engine()
    history = [
        {"overall_score": 0.10, "dimensions": {"isolation": {"score": 0.10}}},
        {"overall_score": 0.20, "dimensions": {"isolation": {"score": 0.20}}},
        {"overall_score": 0.40, "dimensions": {"isolation": {"score": 0.40}}},
    ]

    with_history = engine.assess_risk(
        text="estoy solo, nadie me quiere",
        emotional_state="soledad",
        history=history,
    )
    without_history = engine.assess_risk(
        text="estoy solo, nadie me quiere",
        emotional_state="soledad",
    )

    assert with_history["overall_score"] >= without_history["overall_score"]
