from __future__ import annotations

import logging
import re
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class ActionType(Enum):
    """Actions ANA can recommend after a risk assessment."""

    RESPOND_EMPATHIC = "respond_empathic"
    ESCALATE_TO_CAREGIVER = "escalate_to_caregiver"
    SUGGEST_EXERCISE = "suggest_exercise"
    REQUEST_PROFESSIONAL_HELP = "request_help"
    MONITOR_INTENSIVELY = "monitor_intensively"
    PROVIDE_RESOURCES = "provide_resources"
    SCHEDULE_CHECK_IN = "schedule_check_in"


class RiskDetector:
    """Multi-dimensional clinical risk assessment with hierarchical action decisions.

    Covers H6 (risk pattern identification) and H4 (emotional change detection).
    """

    _WEIGHTS: dict[str, float] = {
        "suicidalidad": 0.35,
        "self_harm": 0.20,
        "hopelessness": 0.15,
        "isolation": 0.12,
        "cognitive_decline": 0.08,
        "substance_abuse": 0.06,
        "sleep_disorder": 0.03,
        "emotional_instability": 0.01,
    }

    _THRESHOLDS: dict[str, tuple[float, float]] = {
        "bajo": (0.0, 0.30),
        "medio": (0.30, 0.55),
        "alto": (0.55, 0.75),
        "critico": (0.75, 1.0),
    }

    _KEYWORDS: dict[str, list[str]] = {
        "suicidalidad": [
            "quiero morir", "voy a matarme", "me suicido", "suicidarme",
            "mejor si no estuviera", "mejor muerto", "no sirvo", "no valgo",
            "no merezco vivir", "ya no puedo seguir", "es hora de irme",
            "todo es sin sentido", "nada importa", "no hay razón para vivir",
        ],
        "self_harm": [
            "cortarme", "arañarme", "golpearme", "hacerme daño",
            "lastrimarme", "herirme", "quemar",
        ],
        "isolation": [
            "estoy solo", "nadie me quiere", "abandonado", "rechazado",
            "no tengo amigos", "completamente aislado", "soy un fardo",
        ],
        "hopelessness": [
            "no hay esperanza", "es imposible", "nada va a cambiar",
            "estoy atrapado", "no hay salida", "nunca mejorará",
        ],
        "cognitive_decline": [
            "no recuerdo", "se me olvida", "confuso", "desorientado",
            "pérdida de memoria", "no puedo pensar",
        ],
        "substance_abuse": [
            "tomé", "bebí", "consumí", "droga", "alcohol", "pastillas",
            "drogadicto", "alcohólico", "adicto",
        ],
        "sleep_disorder": [
            "no puedo dormir", "insomnio", "despierto toda la noche",
            "pesadillas", "no duermo", "duermo mal",
        ],
        "emotional_instability": [
            "cambios de humor", "explosiones de ira", "ansioso", "pánico",
            "ataque de nervios", "descontrol emocional", "muy irritable",
        ],
    }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def assess(
        self,
        text: str,
        emotional_state: str,
        history: Optional[list[dict]] = None,
        user_profile: Optional[dict] = None,
    ) -> dict[str, Any]:
        """Evaluates multi-dimensional clinical risk.

        Args:
            text: User message.
            emotional_state: Current detected emotional state.
            history: Previous risk assessments for trend detection.
            user_profile: User metadata (age, prior history).

        Returns:
            Dict with overall_score, risk_level, dimensions, flags.
        """
        if not text or len(text.strip()) < 3:
            return self._empty_assessment()

        history = history or []
        user_profile = user_profile or {}
        text_lower = text.lower()

        dimension_scores: dict[str, float] = {}
        for dim in self._WEIGHTS:
            dimension_scores[dim] = self._assess_dimension(
                dim, text_lower, emotional_state, history, user_profile
            )

        overall = self._weighted_score(dimension_scores)
        overall = self._apply_contextual(overall, dimension_scores, history)
        risk_level = self._risk_level(overall, dimension_scores)

        return {
            "overall_score": round(overall, 2),
            "risk_level": risk_level,
            "dimensions": {
                d: {
                    "score": round(s, 2),
                    "severity": self._score_to_severity(s),
                }
                for d, s in dimension_scores.items()
            },
            "alert_threshold_exceeded": overall >= 0.55,
            "requires_escalation": (
                overall >= 0.75 or dimension_scores.get("suicidalidad", 0) >= 0.45
            ),
            "critical_dimensions": [d for d, s in dimension_scores.items() if s >= 0.60],
        }

    def decide(
        self,
        current_analysis: dict,
        user_history: Optional[list[dict]] = None,
        user_profile: Optional[dict] = None,
    ) -> tuple[ActionType, dict]:
        """Determines the recommended action based on the current analysis.

        Args:
            current_analysis: Dict with emotional_state and risk_level.
            user_history: Optional history for trend detection.
            user_profile: Optional profile with loneliness_score, etc.

        Returns:
            Tuple of (ActionType, details_dict).
        """
        user_history = user_history or []
        user_profile = user_profile or {}

        risk_score = self._clinical_risk_score(current_analysis, user_history)
        is_declining = self._detect_decline(user_history)
        is_isolated = user_profile.get("loneliness_score", 0) > 0.70

        if risk_score >= 0.75:
            return ActionType.ESCALATE_TO_CAREGIVER, {
                "reason": "Riesgo crítico detectado",
                "risk_score": risk_score,
                "severity": "CRITICAL",
            }
        if risk_score >= 0.60 and is_isolated:
            return ActionType.ESCALATE_TO_CAREGIVER, {
                "reason": "Riesgo alto + aislamiento social",
                "risk_score": risk_score,
                "severity": "HIGH",
            }
        if risk_score >= 0.60:
            return ActionType.MONITOR_INTENSIVELY, {
                "reason": "Riesgo alto detectado",
                "risk_score": risk_score,
                "severity": "HIGH",
            }
        if is_declining and is_isolated:
            return ActionType.SUGGEST_EXERCISE, {
                "reason": "Declive emocional + aislamiento detectados",
                "severity": "MEDIUM",
            }
        if is_declining:
            return ActionType.MONITOR_INTENSIVELY, {
                "reason": "Tendencia emocional declinante",
                "severity": "MEDIUM",
            }
        if is_isolated:
            return ActionType.PROVIDE_RESOURCES, {
                "reason": "Soledad detectada",
                "severity": "MEDIUM",
            }
        if current_analysis.get("emotional_state") == "deprimido":
            return ActionType.REQUEST_PROFESSIONAL_HELP, {
                "reason": "Estado depresivo reportado",
                "severity": "MEDIUM",
            }
        return ActionType.RESPOND_EMPATHIC, {
            "reason": "Análisis dentro de parámetros normales",
            "severity": "LOW",
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _assess_dimension(
        self,
        dimension: str,
        text: str,
        emotional_state: str,
        history: list[dict],
        user_profile: dict,
    ) -> float:
        patterns = self._KEYWORDS.get(dimension, [])
        matches = self._count_matches(text, patterns)
        if dimension == "suicidalidad":
            score = min(matches * 0.30, 0.80)
        else:
            score = min(matches * 0.20, 0.60)
        if matches >= 2:
            score += 0.20 if dimension == "suicidalidad" else 0.15
        score += self._emotion_boost(dimension, emotional_state)
        score += self._history_boost(dimension, history)
        score += self._profile_boost(dimension, user_profile)
        return min(score, 1.0)

    @staticmethod
    def _count_matches(text: str, patterns: list[str]) -> int:
        count = 0
        for p in patterns:
            if p in text:
                count += 1
            elif len(p.split()) > 1 and all(w in text for w in p.split()):
                count += 1
        return count

    @staticmethod
    def _emotion_boost(dimension: str, emotional_state: str) -> float:
        boosts: dict[str, dict[str, float]] = {
            "suicidalidad": {"deprimido": 0.25, "tristeza": 0.20, "soledad": 0.15},
            "self_harm": {"ira": 0.25, "soledad": 0.15},
            "isolation": {"tristeza": 0.20, "soledad": 0.35, "deprimido": 0.25},
            "hopelessness": {"deprimido": 0.30, "tristeza": 0.25, "soledad": 0.20},
            "sleep_disorder": {"ansioso": 0.20},
            "cognitive_decline": {"confuso": 0.30, "ansioso": 0.15},
            "substance_abuse": {"ira": 0.15, "deprimido": 0.15},
            "emotional_instability": {"ira": 0.25, "ansioso": 0.25},
        }
        return boosts.get(dimension, {}).get(emotional_state, 0.0)

    @staticmethod
    def _history_boost(dimension: str, history: list[dict]) -> float:
        if len(history) < 2:
            return 0.0
        recent = history[-3:]
        scores = [r.get("dimensions", {}).get(dimension, {}).get("score", 0) for r in recent]
        if len(scores) >= 2 and scores[-1] - scores[0] > 0.2:
            return 0.10
        if len(scores) >= 2 and scores[-1] - scores[0] > 0.1:
            return 0.05
        return 0.0

    @staticmethod
    def _profile_boost(dimension: str, user_profile: dict) -> float:
        boost = 0.0
        age = user_profile.get("age", 0)
        if age > 65 and dimension == "suicidalidad":
            boost += 0.08
        if user_profile.get("suicidio_previo") and dimension == "suicidalidad":
            boost += 0.15
        if user_profile.get("depression_history") and dimension in ("suicidalidad", "hopelessness"):
            boost += 0.10
        return min(boost, 0.20)

    def _weighted_score(self, dimension_scores: dict[str, float]) -> float:
        return min(sum(s * self._WEIGHTS.get(d, 0) for d, s in dimension_scores.items()), 1.0)

    @staticmethod
    def _apply_contextual(
        base: float, dimension_scores: dict[str, float], history: list[dict]
    ) -> float:
        adjusted = base
        suicidalidad = dimension_scores.get("suicidalidad", 0)
        if suicidalidad >= 0.60:
            adjusted = max(adjusted, suicidalidad * 0.85)
        high_dims = sum(1 for s in dimension_scores.values() if s >= 0.50)
        if high_dims >= 3:
            adjusted = min(adjusted + 0.10, 1.0)
        if len(history) >= 2:
            prev = [h.get("overall_score", 0) for h in history[-3:]]
            if prev and prev[-1] - (sum(prev) / len(prev)) > 0.15:
                adjusted = min(adjusted + 0.05, 1.0)
        return min(adjusted, 1.0)

    @staticmethod
    def _risk_level(overall: float, dimension_scores: dict[str, float]) -> str:
        if overall >= 0.75 or dimension_scores.get("suicidalidad", 0) >= 0.65:
            return "critico"
        if overall >= 0.55 or dimension_scores.get("self_harm", 0) >= 0.60:
            return "alto"
        if overall >= 0.30:
            return "medio"
        return "bajo"

    @staticmethod
    def _clinical_risk_score(current_analysis: dict, user_history: list[dict]) -> float:
        score = 0.0
        risk_map = {"bajo": 0.0, "medio": 0.25, "alto": 0.50}
        score += risk_map.get(current_analysis.get("risk_level", "bajo"), 0.0)
        neg_emotions = {
            "tristeza": 0.15, "miedo": 0.15, "ira": 0.10,
            "deprimido": 0.20, "ansioso": 0.15,
        }
        score += neg_emotions.get(current_analysis.get("emotional_state", "neutral"), 0.0)
        return min(score, 1.0)

    @staticmethod
    def _detect_decline(user_history: list[dict]) -> bool:
        if len(user_history) < 5:
            return False
        values = {
            "alegria": 2, "felicidad": 2, "neutral": 0,
            "ansiedad": -1, "tristeza": -2, "soledad": -2, "deprimido": -2.5,
        }
        recent = [values.get(h.get("emotional_state", "neutral"), 0) for h in user_history[-5:]]
        avg = sum(recent) / len(recent)
        return recent[-1] < (avg * 0.8) and avg < 0

    def _empty_assessment(self) -> dict[str, Any]:
        return {
            "overall_score": 0.0,
            "risk_level": "bajo",
            "dimensions": {d: {"score": 0.0, "severity": "bajo"} for d in self._WEIGHTS},
            "alert_threshold_exceeded": False,
            "requires_escalation": False,
            "critical_dimensions": [],
        }

    @staticmethod
    def _score_to_severity(score: float) -> str:
        if score >= 0.75:
            return "crítico"
        if score >= 0.55:
            return "alto"
        if score >= 0.30:
            return "medio"
        return "bajo"
