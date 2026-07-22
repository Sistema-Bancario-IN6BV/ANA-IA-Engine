from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from api.v1.dependencies import get_emotion_analyzer, get_risk_detector
from core.exceptions import AnalysisError
from modules.emotion.analyzer import EmotionAnalyzer
from modules.emotion.risk_detector import RiskDetector
from modules.emotion.schemas import AnalysisRequest

logger = logging.getLogger(__name__)
router = APIRouter(tags=["emotion"])


@router.post("/analyze")
def analyze(
    request: AnalysisRequest,
    analyzer: EmotionAnalyzer = Depends(get_emotion_analyzer),
    risk_detector: RiskDetector = Depends(get_risk_detector),
) -> dict:
    """Full psychological analysis with risk assessment and action recommendation.

    Maintains backward compatibility with the original POST /analyze contract
    expected by ANA-Backend.
    """
    try:
        analysis = analyzer.analyze(request.text)
    except AnalysisError as exc:
        logger.error("Analysis failed: %s", exc.message)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=exc.message
        )

    risk = risk_detector.assess(
        text=request.text,
        emotional_state=analysis.get("emotional_state", "neutral"),
    )
    action, action_details = risk_detector.decide(
        current_analysis={
            "emotional_state": analysis.get("emotional_state"),
            "risk_level": risk.get("risk_level", "bajo"),
            "sentiment_label": analysis.get("sentiment_label"),
        }
    )

    analysis["risk_level"] = risk.get("risk_level", analysis.get("risk_level"))

    return {
        "analysis": analysis,
        "risk_assessment": {
            "overall_score": risk.get("overall_score", 0),
            "risk_level": risk.get("risk_level"),
            "alert_threshold_exceeded": risk.get("alert_threshold_exceeded", False),
            "requires_escalation": risk.get("requires_escalation", False),
        },
        "decision": {
            "action": action.value,
            "reasoning": action_details.get("reason", "Análisis completado"),
            "severity": action_details.get("severity", "LOW"),
        },
    }
