import random


class Personality:

    def __init__(self, user_profile):
        self.user = user_profile

    def generate_response(self, content: str) -> str:
        tone_prefix = self._get_tone_prefix()
        adjusted_content = self._adjust_length(content)
        emotional_touch = self._emotional_layer()

        return f"{tone_prefix}{adjusted_content}{emotional_touch}"

    def _get_tone_prefix(self):
        if self.user.formality_level >= 7:
            return "Estimado, "
        elif self.user.formality_level <= 3:
            return "Querido, "
        else:
            return ""

    def _adjust_length(self, content):
        if self.user.conversation_level <= 3:
            return content.split(".")[0] + "."
        elif self.user.conversation_level >= 7:
            return content + " ¿Le gustaría contarme un poco más?"
        else:
            return content

    def _emotional_layer(self):
        if self.user.emotional_state == "triste":
            return " Estoy aquí para usted."
        elif self.user.emotional_state == "feliz":
            return " Me alegra mucho escuchar eso."
        elif self.user.emotional_state == "ansioso":
            return " Respire profundo, todo está bien."
        else:
            return ""
