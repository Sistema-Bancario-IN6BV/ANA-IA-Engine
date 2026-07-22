"""Voice service: STT via Groq Whisper + TTS via ElevenLabs (or edge-tts fallback)."""

import io
import os
from pathlib import Path

import httpx

# Load .env before reading env vars — pydantic-settings reads into the model
# but does NOT write to os.environ, so explicit dotenv load is needed here.
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=False)
except ImportError:
    pass

GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
ELEVENLABS_API_KEY: str = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID: str = os.getenv("ELEVENLABS_VOICE_ID", "EXAVITQu4vr4xnSDxMaL")

_STT_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
_STT_MODEL = "whisper-large-v3-turbo"

_ELEVENLABS_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

# edge-tts fallback voices (female, per ISO-639-1)
_EDGE_VOICES: dict[str, str] = {
    "es": "es-ES-ElviraNeural",
    "en": "en-US-JennyNeural",
    "pt": "pt-BR-FranciscaNeural",
    "fr": "fr-FR-DeniseNeural",
    "de": "de-DE-KatjaNeural",
    "it": "it-IT-ElsaNeural",
}
_EDGE_DEFAULT = "es-ES-ElviraNeural"


async def transcribe(audio_bytes: bytes, filename: str = "audio.mp3") -> dict:
    """STT → {text, language, duration} via Groq Whisper API."""
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY no configurada — STT no disponible")

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            _STT_URL,
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
            data={"model": _STT_MODEL, "response_format": "verbose_json"},
            files={"file": (filename, audio_bytes)},
        )
        resp.raise_for_status()

    data = resp.json()
    return {
        "text": data.get("text", "").strip(),
        "language": data.get("language", "es"),
        "duration": data.get("duration", 0.0),
    }


async def _synthesize_elevenlabs(text: str) -> bytes:
    """TTS via ElevenLabs eleven_multilingual_v2 — warm, human-sounding voice."""
    url = _ELEVENLABS_TTS_URL.format(voice_id=ELEVENLABS_VOICE_ID)
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            url,
            headers={
                "xi-api-key": ELEVENLABS_API_KEY,
                "Content-Type": "application/json",
            },
            json={
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.8,
                    "similarity_boost": 0.85,
                    "use_speaker_boost": True,
                },
            },
        )
        resp.raise_for_status()
    return resp.content


async def _synthesize_edge(text: str, language: str = "es") -> bytes:
    """TTS via edge-tts (Microsoft Neural, free, no API key)."""
    try:
        import edge_tts  # noqa: PLC0415
    except ImportError:
        raise RuntimeError("edge-tts no instalado; ejecuta: pip install edge-tts")

    voice = _EDGE_VOICES.get(language, _EDGE_DEFAULT)
    buf = io.BytesIO()
    communicate = edge_tts.Communicate(text, voice)
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            buf.write(chunk["data"])

    audio = buf.getvalue()
    if not audio:
        raise RuntimeError(f"edge-tts no generó audio para voice={voice}")
    return audio


async def synthesize(text: str, language: str = "es") -> bytes:
    """TTS → MP3 bytes. Uses ElevenLabs if key is configured, else edge-tts."""
    if ELEVENLABS_API_KEY:
        return await _synthesize_elevenlabs(text)
    return await _synthesize_edge(text, language)
