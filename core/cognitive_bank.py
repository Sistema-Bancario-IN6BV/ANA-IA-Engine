import random


class CognitiveBank:

    def __init__(self):
        self.memory_questions = [
            "¿Qué comió ayer en el almuerzo?",
            "¿Recuerda el nombre de un amigo de su infancia?",
            "¿Cuál fue su primer trabajo?",
            "¿Puede decirme tres frutas diferentes?"
        ]

        self.math_exercises = [
            "¿Cuánto es 7 más 5?",
            "¿Cuánto es 15 menos 4?",
            "¿Cuánto es 9 por 3?"
        ]

        self.word_games = [
            "Dígame una palabra que empiece con la letra M.",
            "¿Puede mencionar tres animales?",
            "Dígame una palabra que rime con 'casa'."
        ]

        self.motivational_phrases = [
            "Cada día es una nueva oportunidad.",
            "Su experiencia es muy valiosa.",
            "Siempre es bueno mantener la mente activa.",
            "Estoy orgullosa de su esfuerzo."
        ]

    def get_memory_question(self):
        return random.choice(self.memory_questions)

    def get_math_exercise(self):
        return random.choice(self.math_exercises)

    def get_word_game(self):
        return random.choice(self.word_games)

    def get_motivational_phrase(self):
        return random.choice(self.motivational_phrases)

    def get_random_exercise(self):
        category = random.choice([
            self.get_memory_question,
            self.get_math_exercise,
            self.get_word_game
        ])
        return category()
