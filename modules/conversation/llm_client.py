from __future__ import annotations

import logging
import random
from typing import Optional

import httpx

from core.config import settings

logger = logging.getLogger(__name__)


class LLMClient:
    """Unified LLM client: Groq primary, template-based fallback.

    Covers H3 (empathic responses).
    """

    def __init__(self, groq_api_key: Optional[str] = None) -> None:
        self._api_key = groq_api_key or settings.groq_api_key
        self._model = settings.groq_model
        self._mode = "Groq" if self._api_key else "Templates"
        self._templates = _TemplateResponder()

    @property
    def mode(self) -> str:
        """Returns the active response mode: "Groq" or "Templates"."""
        return self._mode

    def generate_response(self, analysis: dict, trend: str = "stable") -> str:
        """Generates an empathic response for the user message.

        Args:
            analysis: Dict returned by EmotionAnalyzer.analyze().
            trend: Emotional trend string for contextual enrichment.

        Returns:
            Empathic response text in Spanish.
        """
        if self._api_key:
            try:
                return self._groq_generate(analysis)
            except Exception as exc:
                logger.warning("Groq API failed, falling back to templates: %s", exc)
                self._mode = "Templates"
        return self._templates.generate_contextual(analysis, trend)

    def _groq_generate(self, analysis: dict) -> str:
        system_prompt = (
            "Eres ANA, asistente empática para adultos mayores. Tu objetivo es acompañar, "
            "validar emociones y brindar apoyo con genuina calidez.\n\n"
            "INSTRUCCIONES:\n"
            "- Valida PRIMERO la emoción del usuario\n"
            "- Sé específico y muestra que realmente entiendes\n"
            "- Tono cálido, cercano, sin tecnicismos\n"
            "- Máximo 2-3 oraciones densas de empatía\n"
            "- Si hay riesgo alto, sugiere apoyo con suavidad\n"
            "- Termina las respuestas limpiamente"
        )
        user_prompt = (
            f"Usuario dijo: \"{analysis.get('text', '').strip()}\"\n\n"
            f"Estado emocional: {analysis.get('emotional_state', 'neutral')}\n"
            f"Sentimiento: {analysis.get('sentiment_label', 'neutral')} "
            f"({analysis.get('sentiment_score', 0.5):.2f})\n"
            f"Riesgo: {analysis.get('risk_level', 'bajo')}\n"
            f"Contexto: {analysis.get('context', 'general')}\n\n"
            "Genera una respuesta empática y natural."
        )
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": 200,
            "temperature": 0.8,
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
        text = resp.json()["choices"][0]["message"]["content"].strip()
        while text.endswith("\\"):
            text = text[:-1].strip()
        return text or "Estoy aquí para ti. ¿Quieres contarme cómo te sientes?"


class _TemplateResponder:
    _BASE: dict[str, list[str]] = {
        "alegria": [
            "Qué alegría me da escucharte así. Me encanta saber que te sientes bien.",
            "Hermoso leer eso, querido. Disfruta este momento con calma y alegría.",
        ],
        "felicidad": [
            "Tu felicidad me alegra mucho. Gracias por compartirlo conmigo.",
        ],
        "tristeza": [
            "Lamento que te sientas así. No estás solo, estoy contigo.",
            "Gracias por contármelo. Te acompaño con cariño en este momento.",
        ],
        "soledad": [
            "Entiendo ese sentimiento. Aquí estoy para hacerte compañía.",
            "No estás solo, querido. Podemos conversar todo el tiempo que quieras.",
        ],
        "ansiedad": [
            "Vamos paso a paso. Respiremos con calma, estoy aquí contigo.",
        ],
        "apatia": [
            "Está bien tener días así. Te acompaño sin prisa.",
        ],
        "neutral": [
            "Te escucho con cariño. Si quieres, seguimos conversando.",
            "Estoy aquí para acompañarte. Cuéntame cómo va tu día.",
        ],
    }
    _RISK_SUFFIX: dict[str, str] = {
        "critico": " Es importante que hablemos con alguien de confianza ahora mismo.",
        "alto": " Si lo ves bien, podemos pedir apoyo a un familiar o profesional de confianza.",
        "medio": " Si necesitas más apoyo, aquí estoy contigo.",
        "bajo": " Seguimos adelante juntos, día a día.",
    }
    _TREND_NOTE: dict[str, str] = {
        "improving": " He notado avance y eso es muy bueno.",
        "declining": " He notado que esta semana ha sido más difícil, y sigo contigo.",
        "unstable": " Sé que el estado de ánimo puede variar. Aquí estaré siempre.",
        "stable": " Me alegra que mantengas estabilidad.",
    }

    def generate_contextual(self, analysis: dict, trend: str) -> str:
        """Generates a template-based contextual response.

        Args:
            analysis: NLP analysis result.
            trend: Emotional trend string.

        Returns:
            Assembled response string.
        """
        emotion = analysis.get("emotional_state", "neutral").lower()
        risk = analysis.get("risk_level", "bajo").lower()
        candidates = self._BASE.get(emotion, self._BASE["neutral"])
        msg = random.choice(candidates)
        msg += self._RISK_SUFFIX.get(risk, "")
        msg += self._TREND_NOTE.get(trend, "")
        return msg
