import asyncio

from fastapi import FastAPI, File, Header, UploadFile
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

import config
from core.analysis_engine import AnalysisEngine
from core.decision_engine import DecisionEngine
from core.interaction_scheduler import InteractionScheduler
from core.response_generator import ResponseGenerator
from core.risk_assessment import RiskAssessmentEngine
from core.routine import RoutineManager
from models.psychological_state import PsychologicalState
from services.groq_service import GroqService
from services.voice_service import synthesize, transcribe

app = FastAPI(title="ANA - Asistente de Análisis Psicológico", version="1.0.0")

analysis_engine = AnalysisEngine()
psy_state = PsychologicalState()

# Inicializar servicios de respuesta
if getattr(config, "GROQ_API_KEY", ""):
    response_service = GroqService()
    response_mode = "Groq"
    use_ai_responses = True
else:
    response_service = ResponseGenerator()
    response_mode = "Templates"
    use_ai_responses = False


class AnalysisRequest(BaseModel):
    text: str


@app.get("/")
def root():
    return {
        "status": "ANA NLP API running",
        "version": "1.0.0",
        "endpoints": {
            "analyze": "/analyze (POST) - Análisis psicológico básico",
            "chat": "/chat (POST) - Análisis + respuesta empática para el abuelo",
            "health": "/health (GET) - Estado del servicio"
        }
    }


@app.get("/health")
def health():
    return {"status": "healthy", "service": "ANA"}


@app.post("/analyze")
async def analyze(request: AnalysisRequest):
    """
    Endpoint avanzado: Análisis completo con riesgo, decisión y scheduling
    Integra: NLP + Risk Assessment + Decision Engine + Scheduling + Routine
    """
    text = request.text
    
    try:
        # 1. NLP Pipeline
        nlp_result = analysis_engine.analyze(text)
        psy_state.register_analysis(nlp_result)
        
        # 2. Evaluación de riesgo (sin historial, basado en análisis actual)
        risk_assessment_engine = RiskAssessmentEngine()
        risk_result = risk_assessment_engine.assess_risk(
            text=text,
            emotional_state=nlp_result.get('emotional_state', 'neutral'),
            history=[],  # Vacío para MVP (sin historial)
            user_profile={}  # Vacío por defecto
        )
        
        # 3. Decisión de acción
        decision_engine = DecisionEngine()
        current_analysis = {
            'emotional_state': nlp_result.get('emotional_state'),
            'risk_level': risk_result.get('risk_level', 'bajo'),
            'sentiment_label': nlp_result.get('sentiment_label')
        }
        action, action_details = decision_engine.determine_action(
            current_analysis=current_analysis,
            user_history=[],  # Vacío para MVP
            user_profile={}   # Vacío por defecto
        )
        
        # 4. Calcular próximo check-in
        scheduler = InteractionScheduler()
        schedule = scheduler.calculate_next_check_in(
            user_profile={},  # Perfil vacío
            last_analysis=current_analysis,
            interaction_history=[]  # Vacío para MVP
        )
        
        # 5. Generar respuesta empática
        trend = psy_state.get_trend()
        if use_ai_responses:
            response_message = response_service.generate_response(nlp_result)
        else:
            response_obj = response_service.generate_contextual_response(nlp_result, trend)
            response_message = response_obj.get('message', 'Entiendo tus sentimientos')
        
        # Retornar respuesta completa
        return {
            'analysis': {
                'sentiment_label': nlp_result.get('sentiment_label'),
                'sentiment': nlp_result.get('sentiment_label'),
                'emotion_model': nlp_result.get('emotion_model'),
                'emotion': nlp_result.get('emotion_model'),
                'emotion_score': nlp_result.get('emotion_score', 0),
                'emotion_dict': nlp_result.get('emotional_state'),
                'emotional_state': nlp_result.get('emotional_state'),
                'semantic_state': nlp_result.get('semantic_state'),
                'semantic_confidence': nlp_result.get('semantic_confidence', 0),
                'context': nlp_result.get('context'),
                'keywords': nlp_result.get('keywords', []),
                'risk_level': risk_result.get('risk_level'),
                'message': response_message,
                'trend': trend,
                'confidence': nlp_result.get('emotion_score', 0)
            },
            'response': response_message,
            'risk_assessment': {
                'overall_score': risk_result.get('overall_score', 0),
                'risk_level': risk_result.get('risk_level'),
                'alert_threshold_exceeded': risk_result.get('alert_threshold_exceeded', False),
                'requires_escalation': risk_result.get('requires_escalation', False)
            },
            'decision': {
                'action': action.value,
                'reasoning': action_details.get('reason', 'Análisis completado'),
                'severity': action_details.get('severity', 'LOW')
            },
            'next_schedule': {
                'next_check_in_time': str(schedule.get('next_check_in_time', '')),
                'strategy': schedule.get('strategy'),
                'interval_minutes': schedule.get('interval_minutes'),
                'is_proactive': schedule.get('is_proactive', False)
            }
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': 'Error al procesar el análisis'
        }


@app.post("/chat")
def chat(request: AnalysisRequest):
    """
    Analiza el texto del abuelo y genera una respuesta empática y cariñosa
    
    Este endpoint:
    1. Realiza el análisis psicológico completo
    2. Registra el estado emocional
    3. Genera una respuesta personalizada, amable y apropiada para una persona mayor
    
    Ideal para interacciones conversacionales con el usuario
    """
    # Realizar análisis
    result = analysis_engine.analyze(request.text)
    psy_state.register_analysis(result)
    trend = psy_state.get_trend()
    
    # Generar respuesta empática — response SIEMPRE es string
    if use_ai_responses:
        response_text = response_service.generate_response(result)
        suggestions = []
    else:
        response_obj = response_service.generate_contextual_response(result, trend)
        response_text = response_obj.get("message", "")
        suggestions = response_obj.get("suggestions", [])

    return {
        # Añade alias "emotion" para compatibilidad con el servicio Node
        "analysis": {**result, "emotion": result.get("emotional_state")},
        "trend": trend,
        "response": response_text,   # Siempre string — el schema Mongo lo requiere
        "suggestions": suggestions,
        "response_mode": response_mode,
    }


@app.post("/voice-chat")
async def voice_chat(
    audio: UploadFile = File(...),
    x_elderly_id: str | None = Header(None, alias="X-Elderly-Id"),
):
    """Audio → JSON: STT (Groq Whisper) + ANA analysis + empathetic response text."""
    audio_bytes = await audio.read()

    stt = await transcribe(audio_bytes, audio.filename or "audio.mp3")
    text: str = stt["text"]
    language: str = stt.get("language", "es")

    if not text:
        return {"wake_word_detected": False, "transcription": ""}

    # CPU-bound HF inference → thread pool (avoids blocking the event loop)
    result: dict = await asyncio.to_thread(analysis_engine.analyze, text)
    psy_state.register_analysis(result)
    trend: str = psy_state.get_trend()

    if use_ai_responses:
        response_text: str = await asyncio.to_thread(
            response_service.generate_response, result, language
        )
    else:
        resp = response_service.generate_contextual_response(result, trend)
        response_text = resp.get("message", "")

    return {
        "wake_word_detected": True,
        "transcription": text,
        "language": language,
        "analysis": {
            "emotion": result.get("emotional_state"),
            "risk_level": result.get("risk_level", "bajo"),
            "keywords": result.get("keywords", []),
            "context": result.get("context"),
            "trend": trend,
        },
        "response": response_text,
        "suggestions": [],
    }


@app.post("/voice-chat/speak")
async def voice_chat_speak(
    audio: UploadFile = File(...),
    x_elderly_id: str | None = Header(None, alias="X-Elderly-Id"),
):
    """Audio → MP3: STT + ANA analysis + TTS (female voice, language-dependent).

    Response headers:
      X-Wake-Word: true | false
      X-Emotion:   detected emotional state
      X-Risk:      risk level (bajo/medio/alto/critico)
      X-Language:  detected language (ISO-639-1)
    """
    audio_bytes = await audio.read()

    stt = await transcribe(audio_bytes, audio.filename or "audio.mp3")
    text: str = stt["text"]
    language: str = stt.get("language", "es")

    if not text:
        return JSONResponse(
            content={"wake_word_detected": False},
            headers={"X-Wake-Word": "false"},
        )

    result: dict = await asyncio.to_thread(analysis_engine.analyze, text)
    psy_state.register_analysis(result)
    trend: str = psy_state.get_trend()

    if use_ai_responses:
        response_text: str = await asyncio.to_thread(
            response_service.generate_response, result, language
        )
    else:
        resp = response_service.generate_contextual_response(result, trend)
        response_text = resp.get("message", "")

    mp3_bytes = await synthesize(response_text, language)

    from urllib.parse import quote  # noqa: PLC0415
    return Response(
        content=mp3_bytes,
        media_type="audio/mpeg",
        headers={
            "X-Wake-Word": "true",
            "X-Emotion": result.get("emotional_state", "neutral"),
            "X-Risk": result.get("risk_level", "bajo"),
            "X-Language": language,
            # URL-encoded so any UTF-8 text is safe in HTTP headers
            "X-Transcription": quote(text[:400]),
            "X-Response": quote(response_text[:400]),
        },
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)