from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from functools import lru_cache
from typing import Optional

from core.config import settings


@dataclass
class Turn:
    """A single conversational turn (user or assistant)."""

    role: str  # "user" | "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    emotion: Optional[str] = None


class ConversationMemory:
    """Short-term sliding window plus emotional trend tracking.

    Covers H2 (session memory) and trend computation used by H4.
    """

    _STATE_VALUES: dict[str, int] = {
        "alegria": 2,
        "felicidad": 2,
        "neutral": 1,
        "ansiedad": -1,
        "tristeza": -2,
        "soledad": -2,
        "apatia": -2,
    }

    def __init__(
        self,
        window_size: Optional[int] = None,
    ) -> None:
        self._window_size = window_size or settings.conversation_window_size
        self._window: list[Turn] = []
        self._long_term_summaries: list[str] = []
        self._emotional_history: list[dict] = []

    def add_turn(self, role: str, content: str, emotion: Optional[str] = None) -> None:
        """Adds a turn to the active window, compressing the oldest when full.

        Args:
            role: "user" or "assistant".
            content: Message text.
            emotion: Optional detected emotional state.
        """
        self._window.append(Turn(role=role, content=content, emotion=emotion))
        if len(self._window) > self._window_size:
            self._compress_oldest()

    def register_analysis(self, analysis: dict) -> None:
        """Records an emotion analysis result for trend computation.

        Args:
            analysis: Dict returned by EmotionAnalyzer.analyze().
        """
        self._emotional_history.append(
            {
                "emotion": analysis.get("emotional_state", "neutral"),
                "intensity": analysis.get("emotion_score", 0),
                "risk": analysis.get("risk_level", "bajo"),
            }
        )
        if len(self._emotional_history) > 20:
            self._emotional_history.pop(0)

    def get_context(self) -> list[dict[str, str]]:
        """Returns current window as an LLM-compatible messages list."""
        return [{"role": t.role, "content": t.content} for t in self._window]

    def get_trend(self) -> str:
        """Computes the emotional trend from the last 5 registered analyses.

        Returns:
            One of: "improving", "declining", "unstable", "stable".
        """
        if len(self._emotional_history) < 3:
            return "stable"
        recent = self._emotional_history[-5:]
        scores = [self._STATE_VALUES.get(e["emotion"], 0) for e in recent]
        avg = sum(scores) / len(scores)
        if scores[-1] > scores[0] and avg > 0:
            return "improving"
        if scores[-1] < scores[0] and avg < 0:
            return "declining"
        if max(scores) - min(scores) >= 3:
            return "unstable"
        return "stable"

    def _compress_oldest(self) -> None:
        oldest = self._window.pop(0)
        self._long_term_summaries.append(f"[{oldest.role}]: {oldest.content[:100]}...")
