from __future__ import annotations

from functools import lru_cache

from modules.conversation.service import ConversationService
from modules.documents.doc_reader import DocReader
from modules.emotion.analyzer import EmotionAnalyzer
from modules.emotion.risk_detector import RiskDetector
from modules.vision.scene_analyzer import SceneAnalyzer


@lru_cache(maxsize=1)
def get_emotion_analyzer() -> EmotionAnalyzer:
    """DI provider for EmotionAnalyzer (loads NLP models on first call)."""
    return EmotionAnalyzer()


@lru_cache(maxsize=1)
def get_risk_detector() -> RiskDetector:
    """DI provider for RiskDetector."""
    return RiskDetector()


@lru_cache(maxsize=1)
def get_conversation_service() -> ConversationService:
    """DI provider for ConversationService (singleton per process)."""
    return ConversationService()


@lru_cache(maxsize=1)
def get_scene_analyzer() -> SceneAnalyzer:
    """DI provider for SceneAnalyzer (loads DETR model on first call)."""
    return SceneAnalyzer()


@lru_cache(maxsize=1)
def get_doc_reader() -> DocReader:
    """DI provider for DocReader."""
    return DocReader()
