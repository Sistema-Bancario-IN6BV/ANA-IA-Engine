from __future__ import annotations

from pydantic import BaseModel


class AnalysisRequest(BaseModel):
    text: str
    user_name: str = ""
    user_age: int = 0


class EmotionAnalysisResult(BaseModel):
    text: str
    sentiment_label: str
    sentiment_score: float
    emotion_model: str
    emotion_score: float
    emotion_dict: str
    semantic_state: str
    semantic_confidence: float
    context: str
    keywords: list[str]
    emotional_state: str
    risk_level: str


class RiskResult(BaseModel):
    overall_score: float
    risk_level: str
    alert_threshold_exceeded: bool
    requires_escalation: bool
    critical_dimensions: list[str]
    dimensions: dict[str, dict]
