"""Servicios de Groq para ANA.

Incluye:
- Generacion de respuestas empaticas para el abuelo.
"""

import re
import httpx
import config

class GroqService:
    """Servicio de Groq para respuestas conversacionales empaticas."""

    def __init__(self) -> None:
        self.api_key = getattr(config, "GROQ_API_KEY", "")
        self.model = getattr(config, "GROQ_MODEL", "llama-3.3-70b-versatile")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY no configurada")

    def _chat_completion(self, messages: list[dict], temperature: float = 0.7, max_tokens: int = 220) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()

        data = response.json()
        return data["choices"][0]["message"]["content"].strip()

    def generate_response(self, analysis: dict, language: str = "es") -> str:
        """Genera una respuesta amable y carinosa basada en el analisis."""
        emotional_state = analysis.get("emotional_state", "neutral")
        sentiment_label = analysis.get("sentiment_label", "neutral")
        sentiment_score = analysis.get("sentiment_score", 0.5)
        risk_level = analysis.get("risk_level", "bajo")
        context = analysis.get("context", "general")
        text = analysis.get("text", "").strip()

        _lang_instructions: dict[str, str] = {
            "es": "Responde siempre en español.",
            "en": "Always respond in English.",
            "pt": "Responde sempre em português.",
            "fr": "Réponds toujours en français.",
            "de": "Antworte immer auf Deutsch.",
            "it": "Rispondi sempre in italiano.",
        }
        lang_instruction = _lang_instructions.get(language, "Responde siempre en español.")

        system_prompt = (
            f"Eres ANA, asistente empatica para adultos mayores. {lang_instruction} "
            "Tu objetivo es acompañar, validar emociones y brindar apoyo con genuine calidez. "
            "\n\nINSTRUCCIONES:\n"
            "- Valida PRIMERO la emoción: reconoce lo que siente (ej: 'Entiendo que te sientas solo')\n"
            "- Sé específico: usa su experiencia para mostrar que realmente entiendes\n"
            "- Ofrece apoyo breve pero meaningful: un consejo práctico, una pregunta de seguimiento o una palabra de ánimo\n"
            "- Mantén un tono cálido, cercano y como si fuera un amigo o familia que le importa\n"
            "- Sin lenguaje técnico ni formalismos. Habla como lo hacen las personas queridas\n"
            "- Máximo 2-3 oraciones, pero densas de empatía. Calidad sobre cantidad\n"
            "- Si menciona riesgo alto (soledad extrema, ideación suicida, abandono): valida con suavidad y sugiere apoyo\n"
            "- Usa nombre si es posible. Personaliza cada respuesta\n"
            "- Si no hay riesgo, fomenta esperanza y conexión\n"
            "- IMPORTANTE: Tus respuestas deben terminar limpiamente sin caracteres incompletos"
        )

        user_prompt = (
            f"Usuario dijo: \"{text}\"\n\n"
            f"Analisis:\n"
            f"- Estado emocional: {emotional_state}\n"
            f"- Sentimiento: {sentiment_label} ({sentiment_score:.2f})\n"
            f"- Riesgo: {risk_level}\n"
            f"- Contexto: {context}\n\n"
            "Genera una respuesta empatica y natural para el abuelo."
        )

        try:
            response = self._chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.8,
                max_tokens=200,
            )
            
            # Limpiar respuesta: eliminar caracteres incompletos como barras invertidas finales
            response = response.strip()
            # Si termina en barra invertida incompleta, removerla
            while response.endswith('\\'):
                response = response[:-1].strip()
            
            return response if response else "Estoy aqui para ti, querido. Si quieres, te escucho con calma."
            
        except Exception as exc:
            print(f"[ERROR] Groq API: {exc}")
            return "Estoy aqui para ti, querido. Si quieres, te escucho con calma."


