from __future__ import annotations

import json
import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from sentence_transformers import SentenceTransformer, util
from transformers import pipeline

from core.config import settings
from core.exceptions import AnalysisError

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _load_sentiment_pipeline():
    return pipeline("sentiment-analysis", model=settings.sentiment_model_name)


@lru_cache(maxsize=1)
def _load_emotion_pipeline():
    return pipeline("text-classification", model=settings.emotion_model_name, top_k=None)


@lru_cache(maxsize=1)
def _load_semantic_model() -> SentenceTransformer:
    return SentenceTransformer(settings.embedding_model_name)


class EmotionAnalyzer:
    """NLP pipeline that classifies emotions, sentiment, and risk level from text.

    Covers H4 (emotional change detection) and H6 (risk pattern analysis).
    """

    def __init__(self) -> None:
        data_dir = settings.data_dir
        self._context_dict = self._load_json(data_dir / "context_dict.json")
        self._emotions_dict = self._load_json(data_dir / "emotions_dict.json")
        self._keywords_dict = self._load_json(data_dir / "keywords_dict.json")
        self._risk_dict = self._load_json(data_dir / "risk_dict.json")
        self._semantic_dict = self._load_json(data_dir / "semantic_states_dict.json")
        self._semantic_embeddings = self._build_semantic_embeddings()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze(self, text: str) -> dict[str, Any]:
        """Runs the full NLP analysis pipeline on the given text.

        Args:
            text: User message to analyze.

        Returns:
            Dict with sentiment, emotion, semantic state, context, keywords,
            emotional_state, and risk_level.

        Raises:
            AnalysisError: If model inference fails unexpectedly.
        """
        if not text.strip():
            return self._empty_response()

        try:
            text_lower = text.lower()

            sentiment = _load_sentiment_pipeline()(text_lower)[0]
            sentiment_label = sentiment["label"].lower()
            sentiment_score = float(sentiment["score"])

            emotion_raw = _load_emotion_pipeline()(text_lower)[0]
            emotion_data = max(emotion_raw, key=lambda x: x["score"])
            emotion_model = emotion_data["label"].lower()
            emotion_score = emotion_data["score"]

            context = self._detect_context(text_lower)
            keywords = self._extract_keywords(text_lower)
            emotion_dict = self._detect_emotion_dict(text_lower)
            semantic_state, semantic_confidence = self._detect_semantic_state(text_lower)
            risk_level = self._assess_risk(text_lower)
            emotional_state = self._fuse_states(
                sentiment_label, emotion_model, emotion_dict, semantic_state
            )

            return {
                "text": text,
                "sentiment_label": sentiment_label,
                "sentiment_score": round(sentiment_score, 4),
                "emotion_model": emotion_model,
                "emotion_score": round(emotion_score, 4),
                "emotion_dict": emotion_dict,
                "semantic_state": semantic_state,
                "semantic_confidence": round(semantic_confidence, 4),
                "context": context,
                "keywords": keywords,
                "emotional_state": emotional_state,
                "risk_level": risk_level,
            }
        except Exception as exc:
            raise AnalysisError(f"Analysis pipeline failed: {exc}") from exc

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_semantic_embeddings(self) -> dict:
        model = _load_semantic_model()
        return {
            state: model.encode(phrases, convert_to_tensor=True)
            for state, phrases in self._semantic_dict.items()
        }

    def _detect_semantic_state(self, text: str) -> tuple[str, float]:
        model = _load_semantic_model()
        embedding = model.encode(text, convert_to_tensor=True)
        best_state, best_score = "neutral", 0.0
        for state, vectors in self._semantic_embeddings.items():
            score = util.cos_sim(embedding, vectors).max().item()
            if score > best_score:
                best_score = score
                best_state = state
        if best_score < 0.65:
            return "neutral", best_score
        return best_state, best_score

    def _detect_context(self, text: str) -> str:
        best_context, best_hits = "general", 0
        for context, words in self._context_dict.items():
            hits = sum(1 for w in words if w in text)
            if hits > best_hits:
                best_hits, best_context = hits, context
        return best_context

    def _detect_emotion_dict(self, text: str) -> str:
        best_emotion, best_hits = "none", 0
        for emotion, words in self._emotions_dict.items():
            hits = sum(1 for w in words if w in text)
            if hits > best_hits:
                best_hits, best_emotion = hits, emotion
        return best_emotion

    def _extract_keywords(self, text: str) -> list[str]:
        found = {w for group in self._keywords_dict.values() for w in group if w in text}
        return list(found)

    def _assess_risk(self, text: str) -> str:
        best_level, best_hits = "bajo", 0
        for level, words in self._risk_dict.items():
            hits = sum(1 for w in words if w in text)
            if hits > best_hits:
                best_hits, best_level = hits, level
        return best_level

    def _fuse_states(
        self, sentiment: str, emotion_model: str, emotion_dict: str, semantic: str
    ) -> str:
        if emotion_dict != "none":
            return emotion_dict
        if semantic != "neutral":
            return semantic
        mapping = {"joy": "alegria", "sadness": "tristeza", "fear": "ansiedad"}
        if emotion_model in mapping:
            return mapping[emotion_model]
        if sentiment == "positive":
            return "alegria"
        if sentiment == "negative":
            return "tristeza"
        return "neutral"

    @staticmethod
    def _load_json(path: Path) -> dict:
        if not path.exists():
            logger.warning("Dictionary not found: %s", path)
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.error("Failed to load %s: %s", path, exc)
            return {}

    @staticmethod
    def _empty_response() -> dict[str, Any]:
        return {
            "text": "",
            "sentiment_label": "neutral",
            "sentiment_score": 0.0,
            "emotion_model": "neutral",
            "emotion_score": 0.0,
            "emotion_dict": "none",
            "semantic_state": "neutral",
            "semantic_confidence": 0.0,
            "context": "general",
            "keywords": [],
            "emotional_state": "neutral",
            "risk_level": "bajo",
        }
