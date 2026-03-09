import datetime


class UserProfile:
    def __init__(self, name="Usuario"):
        self.name = name

        # Preferencias sociales
        self.talkativeness = 0.5  # 0 = poco hablador, 1 = muy hablador
        self.formality = 0.5      # 0 = informal, 1 = formal

        # Estado emocional acumulado
        self.emotional_history = []
        self.current_emotion = "neutral"

        # Métricas de bienestar
        self.loneliness_score = 0.3
        self.cognitive_risk_score = 0.2
        self.interaction_level = 0.5

        # Tiempos
        self.last_interaction = datetime.datetime.now()

    def update_interaction_time(self):
        self.last_interaction = datetime.datetime.now()

    def add_emotion(self, emotion):
        self.emotional_history.append(emotion)
        self.current_emotion = emotion

        # Mantener solo últimas 20 emociones
        if len(self.emotional_history) > 20:
            self.emotional_history.pop(0)

    def adjust_talkativeness(self, value):
        self.talkativeness = min(max(value, 0), 1)

    def adjust_formality(self, value):
        self.formality = min(max(value, 0), 1)