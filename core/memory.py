import json
import os
from datetime import datetime
from models.user_profile import UserProfile


class Memory:

    def __init__(self, filepath="data/user_memory.json"):
        self.filepath = filepath
        self.user_profile = None
        self.data = {}
        self.load_memory()

    def load_memory(self):
        if not os.path.exists(self.filepath):
            raise FileNotFoundError("Archivo de memoria no encontrado.")

        with open(self.filepath, "r", encoding="utf-8") as file:
            self.data = json.load(file)

        self.user_profile = UserProfile(
            name=self.data.get("name", "Usuario"),
            conversation_level=self.data.get("conversation_level", 5),
            formality_level=self.data.get("formality_level", 5),
            activity_level=self.data.get("activity_level", 5),
            emotional_state=self.data.get("emotional_state", "neutral"),
            preferences=self.data.get("preferences", [])
        )

    def save_memory(self):
        self.data.update({
            "name": self.user_profile.name,
            "conversation_level": self.user_profile.conversation_level,
            "formality_level": self.user_profile.formality_level,
            "activity_level": self.user_profile.activity_level,
            "emotional_state": self.user_profile.emotional_state,
            "preferences": self.user_profile.preferences
        })

        with open(self.filepath, "w", encoding="utf-8") as file:
            json.dump(self.data, file, indent=4, ensure_ascii=False)

    def register_conversation(self, user_input, ana_response):
        conversation_entry = {
            "timestamp": datetime.now().isoformat(),
            "user": user_input,
            "ana": ana_response
        }

        self.data["conversations"].append(conversation_entry)
        self.data["last_interaction"] = datetime.now().isoformat()

        self.save_memory()

    def register_symptom(self, symptom):
        self.data["symptoms"].append({
            "timestamp": datetime.now().isoformat(),
            "symptom": symptom
        })

        self.save_memory()
