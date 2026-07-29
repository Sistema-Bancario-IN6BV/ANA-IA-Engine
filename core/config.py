from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent  # ANA-IA-Engine/


class Settings(BaseSettings):
    """Centralizes all ANA-IA-Engine configuration from environment variables or .env."""

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "ANA - Asistente de Acompañamiento"
    debug: bool = False

    # LLM (Groq) — falls back to templates if absent
    groq_api_key: Optional[str] = None
    groq_model: str = "llama-3.3-70b-versatile"

    # TTS — ElevenLabs (falls back to edge-tts if absent)
    # Voice ID default: "Bella" (multilingual, warm female voice)
    elevenlabs_api_key: Optional[str] = None
    elevenlabs_voice_id: str = "EXAVITQu4vr4xnSDxMaL"

    # HuggingFace
    huggingface_api_key: Optional[str] = None

    # NLP models
    emotion_model_name: str = "SamLowe/roberta-base-go_emotions"
    sentiment_model_name: str = "cardiffnlp/twitter-xlm-roberta-base-sentiment"
    embedding_model_name: str = "all-MiniLM-L6-v2"

    # Vision
    vision_model_name: str = "facebook/detr-resnet-50"
    vision_device: str = "cpu"
    vision_confidence_threshold: float = 0.7

    # Documents / OCR
    document_model_name: str = "microsoft/layoutlmv3-base"
    ocr_language: str = "spa"
    # Only needed if `tesseract` isn't on PATH (e.g. a non-default Windows install).
    # Leave unset on Linux/Docker/macOS where it's typically already on PATH.
    ocr_tesseract_cmd: Optional[str] = None

    # Conversation memory
    conversation_window_size: int = 10

    # Scheduling / thresholds
    proactive_interval_minutes: int = 90
    inactivity_threshold_minutes: int = 120
    loneliness_alert_threshold: float = 0.7
    emotion_decline_threshold: float = 0.65

    @computed_field
    @property
    def data_dir(self) -> Path:
        return BASE_DIR / "data"


settings = Settings()
