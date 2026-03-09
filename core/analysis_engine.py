import json
import os

from transformers import pipeline
from sentence_transformers import SentenceTransformer, util


class AnalysisEngine:

    def __init__(self):

        base_path = os.path.join(os.getcwd(), "data")

        # ===============================
        # MODELOS IA
        # ===============================

        self.semantic_model = SentenceTransformer("all-MiniLM-L6-v2")

        self.sentiment_model = pipeline(
            "sentiment-analysis",
            model="cardiffnlp/twitter-xlm-roberta-base-sentiment"
        )

        self.emotion_model = pipeline(
            "text-classification",
            model="SamLowe/roberta-base-go_emotions",
            top_k=None
        )

        # ===============================
        # DICCIONARIOS
        # ===============================

        self.context_dict = self._load_json(os.path.join(base_path, "context_dict.json"))
        self.emotions_dict = self._load_json(os.path.join(base_path, "emotions_dict.json"))
        self.keywords_dict = self._load_json(os.path.join(base_path, "keywords_dict.json"))
        self.risk_dict = self._load_json(os.path.join(base_path, "risk_dict.json"))
        self.semantic_dict = self._load_json(os.path.join(base_path, "semantic_states_dict.json"))

        # ===============================
        # PREPROCESAMIENTO
        # ===============================

        self.semantic_embeddings = self._build_semantic_embeddings()

    # =========================================================
    # MÉTODO PRINCIPAL
    # =========================================================

    def analyze(self, text):

        if not text.strip():
            return self._empty_response()

        text_lower = text.lower()

        # -----------------------------
        # SENTIMIENTO
        # -----------------------------

        sentiment = self.sentiment_model(text_lower)[0]

        sentiment_label = sentiment["label"].lower()
        sentiment_score = float(sentiment["score"])

        # -----------------------------
        # EMOCIÓN (modelo IA)
        # -----------------------------

        emotion_raw = self.emotion_model(text_lower)[0]

        emotion_data = max(emotion_raw, key=lambda x: x["score"])

        emotion_model = emotion_data["label"].lower()
        emotion_score = emotion_data["score"]

        # -----------------------------
        # CONTEXTO
        # -----------------------------

        context = self._detect_context(text_lower)

        # -----------------------------
        # KEYWORDS
        # -----------------------------

        keywords = self._extract_keywords(text_lower)

        # -----------------------------
        # EMOCIONES POR DICCIONARIO
        # -----------------------------

        emotion_dict = self._detect_emotion_dict(text_lower)

        # -----------------------------
        # ESTADO SEMÁNTICO
        # -----------------------------

        semantic_state, semantic_confidence = self._detect_semantic_state(text_lower)

        # -----------------------------
        # RIESGO
        # -----------------------------

        risk_level = self._assess_risk(text_lower)

        # -----------------------------
        # FUSIÓN FINAL
        # -----------------------------

        emotional_state = self._fuse_states(
            sentiment_label,
            emotion_model,
            emotion_dict,
            semantic_state
        )

        return {

            "text": text,

            "sentiment_label": sentiment_label,
            "sentiment_score": round(sentiment_score, 4),

            "emotion_model": emotion_model,
            "emotion_score": round(emotion_score, 4),

            "emotion_dict": emotion_dict,

            "semantic_state": semantic_state,
            "semantic_confidence": round(semantic_confidence, 4),

            "context": context,

            "keywords": keywords,

            "emotional_state": emotional_state,

            "risk_level": risk_level
        }

    # =========================================================
    # EMBEDDINGS SEMÁNTICOS
    # =========================================================

    def _build_semantic_embeddings(self):

        embeddings = {}

        for state, phrases in self.semantic_dict.items():

            embeddings[state] = self.semantic_model.encode(
                phrases,
                convert_to_tensor=True
            )

        return embeddings

    # =========================================================
    # DETECTAR ESTADO SEMÁNTICO
    # =========================================================

    def _detect_semantic_state(self, text):

        embedding = self.semantic_model.encode(
            text,
            convert_to_tensor=True
        )

        best_state = "neutral"
        best_score = 0

        for state, vectors in self.semantic_embeddings.items():

            similarity = util.cos_sim(embedding, vectors)

            score = similarity.max().item()

            if score > best_score:

                best_score = score
                best_state = state

        if best_score < 0.65:
            return "neutral", best_score

        return best_state, best_score

    # =========================================================
    # DETECTAR CONTEXTO
    # =========================================================

    def _detect_context(self, text):

        best_context = "general"
        best_hits = 0

        for context, words in self.context_dict.items():

            hits = sum(1 for word in words if word in text)

            if hits > best_hits:

                best_hits = hits
                best_context = context

        return best_context

    # =========================================================
    # DETECTAR EMOCIÓN POR DICCIONARIO
    # =========================================================

    def _detect_emotion_dict(self, text):

        best_emotion = "none"
        best_hits = 0

        for emotion, words in self.emotions_dict.items():

            hits = sum(1 for word in words if word in text)

            if hits > best_hits:

                best_hits = hits
                best_emotion = emotion

        return best_emotion

    # =========================================================
    # KEYWORDS
    # =========================================================

    def _extract_keywords(self, text):

        found = []

        for group in self.keywords_dict.values():

            for word in group:

                if word in text:
                    found.append(word)

        return list(set(found))

    # =========================================================
    # RISK DETECTION
    # =========================================================

    def _assess_risk(self, text):

        best_level = "bajo"
        best_hits = 0

        for level, words in self.risk_dict.items():

            hits = sum(1 for word in words if word in text)

            if hits > best_hits:

                best_hits = hits
                best_level = level

        return best_level

    # =========================================================
    # FUSIÓN FINAL DE ESTADOS
    # =========================================================

    def _fuse_states(self, sentiment, emotion_model, emotion_dict, semantic):

        if emotion_dict != "none":
            return emotion_dict

        if semantic != "neutral":
            return semantic

        if emotion_model == "joy":
            return "alegria"

        if emotion_model == "sadness":
            return "tristeza"

        if emotion_model == "fear":
            return "ansiedad"

        if sentiment == "positive":
            return "alegria"

        if sentiment == "negative":
            return "tristeza"

        return "neutral"

    # =========================================================
    # CARGAR JSON
    # =========================================================

    def _load_json(self, path):

        if not os.path.exists(path):

            print(f"[WARNING] No existe: {path}")
            return {}

        try:

            with open(path, "r", encoding="utf-8") as f:

                return json.load(f)

        except Exception as e:

            print(f"[ERROR] {path} -> {e}")
            return {}

    # =========================================================
    # RESPUESTA VACÍA
    # =========================================================

    def _empty_response(self):

        return {

            "text": "",

            "sentiment_label": "neutral",
            "sentiment_score": 0,

            "emotion_model": "neutral",
            "emotion_score": 0,

            "emotion_dict": "none",

            "semantic_state": "neutral",
            "semantic_confidence": 0,

            "context": "general",

            "keywords": [],

            "emotional_state": "neutral",

            "risk_level": "bajo"
        }