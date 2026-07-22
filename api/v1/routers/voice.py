from __future__ import annotations

import asyncio
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Header, UploadFile
from fastapi.responses import JSONResponse, Response

from api.v1.dependencies import get_conversation_service
from modules.conversation.service import ConversationService
from services.voice_service import synthesize, transcribe

router = APIRouter(tags=["voice"])


@router.post("/voice-chat")
async def voice_chat(
    audio: UploadFile = File(...),
    x_elderly_id: str | None = Header(None, alias="X-Elderly-Id"),
    service: ConversationService = Depends(get_conversation_service),
) -> dict:
    """Audio → JSON: STT (Groq Whisper) + ANA analysis + empathetic response text."""
    audio_bytes = await audio.read()
    stt = await transcribe(audio_bytes, audio.filename or "audio.mp3")
    text: str = stt["text"]
    language: str = stt.get("language", "es")

    if not text:
        return {"wake_word_detected": False, "transcription": ""}

    chat_result = await asyncio.to_thread(service.chat, text)
    analysis = chat_result.analysis
    trend = chat_result.trend
    response = chat_result.response
    response_text = response["message"] if isinstance(response, dict) else response

    return {
        "wake_word_detected": True,
        "transcription": text,
        "language": language,
        "analysis": {
            "emotion": analysis.get("emotional_state"),
            "risk_level": analysis.get("risk_level", "bajo"),
            "keywords": analysis.get("keywords", []),
            "context": analysis.get("context"),
            "trend": trend,
        },
        "response": response_text,
        "suggestions": [],
    }


@router.post("/voice-chat/speak")
async def voice_chat_speak(
    audio: UploadFile = File(...),
    x_elderly_id: str | None = Header(None, alias="X-Elderly-Id"),
    service: ConversationService = Depends(get_conversation_service),
) -> Response:
    """Audio → MP3: STT + ANA analysis + TTS (female voice, language-dependent)."""
    audio_bytes = await audio.read()
    stt = await transcribe(audio_bytes, audio.filename or "audio.mp3")
    text: str = stt["text"]
    language: str = stt.get("language", "es")

    if not text:
        return JSONResponse(
            content={"wake_word_detected": False},
            headers={"X-Wake-Word": "false"},
        )

    chat_result = await asyncio.to_thread(service.chat, text)
    analysis = chat_result.analysis
    response = chat_result.response
    response_text = response["message"] if isinstance(response, dict) else response

    mp3_bytes = await synthesize(response_text, language)

    return Response(
        content=mp3_bytes,
        media_type="audio/mpeg",
        headers={
            "X-Wake-Word": "true",
            "X-Emotion": analysis.get("emotional_state", "neutral"),
            "X-Risk": analysis.get("risk_level", "bajo"),
            "X-Language": language,
            "X-Transcription": quote(text[:400]),
            "X-Response": quote(response_text[:400]),
        },
    )
