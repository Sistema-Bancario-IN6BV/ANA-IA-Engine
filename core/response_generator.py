import random


class ResponseGenerator:
    """Genera respuestas amables para el usuario (abuelo)."""

    def __init__(self) -> None:
        self.base_by_emotion = {
            "alegria": [
                "Que alegria me da escucharte asi. Me encanta saber que te sientes bien.",
                "Hermoso leer eso, querido. Disfruta este momento con calma y alegria.",
            ],
            "felicidad": [
                "Tu felicidad me alegra mucho. Gracias por compartirlo conmigo.",
                "Que lindo que te sientas asi. Estoy aqui para acompanarte siempre.",
            ],
            "tristeza": [
                "Lamento que te sientas asi. No estas solo, estoy contigo.",
                "Gracias por contarmelo. Te acompano con carino en este momento.",
            ],
            "soledad": [
                "Entiendo ese sentimiento. Aqui estoy para hacerte compania.",
                "No estas solo, querido. Podemos conversar todo el tiempo que quieras.",
            ],
            "ansiedad": [
                "Vamos paso a paso. Respiremos con calma, estoy aqui contigo.",
                "Te acompano en esto. Podemos tomarlo con tranquilidad.",
            ],
            "apatia": [
                "Esta bien tener dias asi. Te acompano sin prisa.",
                "No pasa nada si hoy hay menos energia. Aqui estoy para ti.",
            ],
            "neutral": [
                "Te escucho con carino. Si quieres, seguimos conversando.",
                "Estoy aqui para acompanarte. Cuentame como va tu dia.",
            ],
        }

        self.risk_suffix = {
            "alto": " Si lo ves bien, podemos pedir apoyo a un familiar o profesional de confianza.",
            "medio": " Si necesitas mas apoyo, aqui estoy contigo.",
            "bajo": " Seguimos adelante juntos, dia a dia.",
        }

    def generate_response(self, analysis: dict) -> str:
        emotion = analysis.get("emotional_state", "neutral").lower()
        risk = analysis.get("risk_level", "bajo").lower()

        candidates = self.base_by_emotion.get(emotion, self.base_by_emotion["neutral"])
        message = random.choice(candidates)
        message += self.risk_suffix.get(risk, "")
        return message

    def generate_contextual_response(self, analysis: dict, trend: str) -> dict:
        message = self.generate_response(analysis)

        trend_note = ""
        if trend == "improving":
            trend_note = " He notado avance y eso es muy bueno."
        elif trend == "declining":
            trend_note = " He notado que esta semana ha sido mas dificil, y sigo contigo."
        else:
            trend_note = " Me alegra que mantengas estabilidad."

        emotional_state = analysis.get("emotional_state", "neutral").lower()

        suggestions = {
            "alegria": ["Aprovecha para hacer algo que disfrutes hoy."],
            "tristeza": ["Si quieres, damos un paseo corto o escuchamos musica tranquila."],
            "ansiedad": ["Probemos respirar profundo tres veces."],
            "soledad": ["Podemos llamar a alguien querido cuando te parezca."],
            "neutral": ["Si quieres, me cuentas como te fue hoy."],
        }.get(emotional_state, ["Estoy aqui para acompanarte."])

        return {
            "message": message + trend_note,
            "tone": "carinoso y empatico",
            "emotional_state_detected": emotional_state,
            "trend": trend,
            "suggestions": suggestions,
        }
