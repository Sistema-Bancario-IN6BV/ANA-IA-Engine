from fastapi import FastAPI
from pydantic import BaseModel
from core.analysis_engine import AnalysisEngine
from models.psychological_state import PsychologicalState
from services.groq_service import GroqService
from core.response_generator import ResponseGenerator
import config

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
def analyze(request: AnalysisRequest):
    """
    Analiza el texto y genera una respuesta empática:
    - Análisis emocional completo
    - Respuesta personalizada (Groq o plantillas)
    - Tendencia histórica
    """
    result = analysis_engine.analyze(request.text)
    psy_state.register_analysis(result)

    # Generar respuesta empática
    if use_ai_responses:
        try:
            ai_response = response_service.generate_response(result)
        except Exception as e:
            print(f"[ERROR] Generando respuesta AI: {e}")
            ai_response = "Estoy aquí para ti. ¿Cómo puedo ayudarte?"
    else:
        ai_response = response_service.generate_response(result)

    return {
        "analysis": result,
        "trend": psy_state.get_trend(),
        "response": ai_response,
        "response_mode": response_mode
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
    
    # Generar respuesta empática
    if use_ai_responses:
        response = {
            "message": response_service.generate_response(result),
            "tone": "carioso y empatico",
            "emotional_state_detected": result.get("emotional_state", "neutral"),
            "trend": trend,
            "suggestions": []
        }
    else:
        response = response_service.generate_contextual_response(result, trend)
    
    return {
        "analysis": result,
        "trend": trend,
        "response": response,
        "response_mode": response_mode
    }