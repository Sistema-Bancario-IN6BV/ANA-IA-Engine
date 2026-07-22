from __future__ import annotations

from modules.conversation.llm_client import LLMClient
from modules.conversation.memory import ConversationMemory
from modules.conversation.schemas import ChatResponse
from modules.emotion.analyzer import EmotionAnalyzer
from modules.emotion.risk_detector import RiskDetector


class ConversationService:
    """Orchestrates the full /chat pipeline for a single user session.

    Covers H1 (conversation), H2 (memory), H3 (empathic responses).
    """

    def __init__(self) -> None:
        self._analyzer = EmotionAnalyzer()
        self._risk_detector = RiskDetector()
        self._memory = ConversationMemory()
        self._llm = LLMClient()

    def chat(self, text: str, user_name: str = "", user_age: int = 0) -> ChatResponse:
        """Runs the full empathic chat pipeline.

        Args:
            text: User message.
            user_name: Optional name for personalization.
            user_age: Optional age for risk profile boosting.

        Returns:
            ChatResponse with analysis, trend, and empathic reply.
        """
        analysis = self._analyzer.analyze(text)
        self._memory.register_analysis(analysis)
        trend = self._memory.get_trend()

        response_text = self._llm.generate_response(analysis, trend)
        response_obj = {
            "message": response_text,
            "tone": "cariñoso y empático",
            "emotional_state_detected": analysis.get("emotional_state", "neutral"),
            "trend": trend,
            "suggestions": self._suggestions(analysis.get("emotional_state", "neutral")),
        }

        self._memory.add_turn("user", text, emotion=analysis.get("emotional_state"))
        self._memory.add_turn("assistant", response_text)

        return ChatResponse(
            analysis=analysis,
            trend=trend,
            response=response_obj,
            response_mode=self._llm.mode,
        )

    @staticmethod
    def _suggestions(emotion: str) -> list[str]:
        mapping = {
            "alegria": ["Aprovecha para hacer algo que disfrutes hoy."],
            "tristeza": ["Si quieres, damos un paseo corto o escuchamos música tranquila."],
            "ansiedad": ["Probemos respirar profundo tres veces."],
            "soledad": ["Podemos llamar a alguien querido cuando te parezca."],
        }
        return mapping.get(emotion, ["Estoy aquí para acompañarte."])
