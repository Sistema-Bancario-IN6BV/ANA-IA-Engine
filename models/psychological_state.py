class PsychologicalState:

    def __init__(self):

        self.history = []

        self.state_values = {

            "alegria": 2,
            "felicidad": 2,

            "neutral": 1,

            "ansiedad": -1,

            "tristeza": -2,
            "soledad": -2,
            "apatia": -2
        }

    def register_analysis(self, analysis):

        context_value = analysis.get("semantic_context", analysis.get("context", "general"))
        intensity_value = analysis.get("emotional_intensity", analysis.get("emotion_score", 0))

        entry = {

            "emotion": analysis.get("emotional_state", "neutral"),
            "context": context_value,
            "intensity": intensity_value,
            "risk": analysis.get("risk_level", "bajo")

        }

        self.history.append(entry)

        if len(self.history) > 20:
            self.history.pop(0)

    def get_trend(self):

        if len(self.history) < 3:
            return "stable"

        recent = self.history[-5:]

        scores = []

        for item in recent:

            emotion = item["emotion"]

            value = self.state_values.get(emotion, 0)

            scores.append(value)

        avg = sum(scores) / len(scores)

        first = scores[0]
        last = scores[-1]

        if last > first and avg > 0:
            return "improving"

        if last < first and avg < 0:
            return "declining"

        if max(scores) - min(scores) >= 3:
            return "unstable"

        return "stable"