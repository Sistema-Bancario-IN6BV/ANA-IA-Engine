"""
Risk Assessment Engine para ANA
Evaluación multi-dimensional de riesgo clínico psicológico
"""

from typing import Dict, Tuple, List, Optional
from enum import Enum
import re
import logging

# Configurar logging
logger = logging.getLogger(__name__)


class RiskDimension(Enum):
    """Dimensiones de evaluación de riesgo"""
    SUICIDALITY = "suicidalidad"           # Riesgo de suicidio
    SELF_HARM = "self_harm"                 # Riesgo de automutilación
    ISOLATION = "isolation"                 # Riesgo de aislamiento social
    COGNITIVE_DECLINE = "cognitive_decline" # Declive cognitivo
    SLEEP_DISORDER = "sleep_disorder"       # Trastorno del sueño
    SUBSTANCE_ABUSE = "substance_abuse"     # Abuso de sustancias
    HOPELESSNESS = "hopelessness"           # Desesperación
    EMOTIONAL_INSTABILITY = "instability"   # Inestabilidad emocional


class RiskLevel(Enum):
    """Niveles de riesgo según score"""
    BAJO = "bajo"           # score < 0.35
    MEDIO = "medio"         # 0.35 <= score < 0.65
    ALTO = "alto"           # score >= 0.65
    CRITICO = "critico"     # score > 0.85 con factores agravantes


class RiskAssessmentEngine:
    """
    Motor de evaluación de riesgo multi-dimensional
    Proporciona análisis profundo de riesgo clínico con validación y contexto histórico
    """

    def __init__(self, enable_debug: bool = False):
        """Inicializa el motor de evaluación de riesgo"""
        self.enable_debug = enable_debug
        self.keyword_patterns = self._load_keyword_patterns()
        self.weights = self._default_weights()
        self.thresholds = self._risk_thresholds()

    @staticmethod
    def _risk_thresholds() -> Dict[str, float]:
        """Define umbrales para niveles de riesgo"""
        return {
            "bajo": (0.0, 0.30),
            "medio": (0.30, 0.55),
            "alto": (0.55, 0.75),
            "critico": (0.75, 1.0)
        }

    @staticmethod
    def _default_weights() -> Dict:
        """Pesos para cada dimensión de riesgo (normalizados a suma total = 1.0)"""
        weights = {
            "suicidalidad": 0.35,          # Máxima prioridad: intentos suicidas
            "self_harm": 0.20,             # Auto-lesiones deliberadas
            "hopelessness": 0.15,          # Desesperación/falta de esperanza
            "isolation": 0.12,             # Aislamiento social
            "cognitive_decline": 0.08,     # Deterioro cognitivo
            "substance_abuse": 0.06,       # Abuso de sustancias
            "sleep_disorder": 0.03,        # Trastornos del sueño
            "emotional_instability": 0.01, # Inestabilidad emocional (menos crítico)
        }
        
        # Validar que sumen a 1.0
        total = sum(weights.values())
        if abs(total - 1.0) > 0.001:
            logger.warning(f"⚠️ Pesos no normalizados: suma={total}")
            # Normalizar automáticamente
            for key in weights:
                weights[key] = weights[key] / total
        
        return weights

    def _load_keyword_patterns(self) -> Dict[str, List[str]]:
        """Carga patrones de palabras clave para cada dimensión"""
        return {
            "suicidalidad": [
                "quiero morir", "voy a matarme", "me suicido", "suicidarme",
                "mejor si no estuviera", "mejor muerto", "no sirvo", "no valgo",
                "no merezco vivir", "ya no puedo seguir", "es hora de irme",
                "todo es sin sentido", "nada importa", "no hay razón para vivir"
            ],
            "self_harm": [
                "cortarme", "arañarme", "golpearme", "hacerme daño",
                "lastrimarme", "herirme", "cauterio", "quemar"
            ],
            "isolation": [
                "estoy solo", "nadie me quiere", "abandonado", "rechazado",
                "no tengo amigos", "completamente aislado", "soy un fardo",
                "mejor estaría sin mi"
            ],
            "hopelessness": [
                "no hay esperanza", "es imposible", "nada va a cambiar",
                "estoy atrapado", "no hay salida", "nunca mejorará"
            ],
            "cognitive_decline": [
                "no recuerdo", "se me olvida", "confuso", "desorientado",
                "pérdida de memoria", "no puedo pensar"
            ],
            "substance_abuse": [
                "tomé", "bebí", "consumí", "droga", "alcohol", "pastillas",
                "drogadicto", "alcohólico", "adicto"
            ],
            "sleep_disorder": [
                "no puedo dormir", "insomnio", "despierto toda la noche",
                "pesadillas", "no duermo", "duermo mal"
            ],
            "emotional_instability": [
                "cambios de humor", "explosiones de ira", "ansioso", "pánico",
                "ataque de nervios", "descontrol emocional", "muy irritable"
            ],
        }

    def assess_risk(
        self,
        text: str,
        emotional_state: str,
        history: Optional[List[Dict]] = None,
        user_profile: Optional[Dict] = None,
        context: Optional[str] = None
    ) -> Dict:
        """
        Realiza evaluación completa de riesgo multi-dimensional
        
        Args:
            text: Texto a evaluar
            emotional_state: Estado emocional actual
            history: Historial previo de análisis
            user_profile: Perfil del usuario (edad, antecedentes, etc.)
            context: Contexto adicional (ambiente, triggers conocidos)
            
        Returns:
            Diccionario con evaluación detallada de riesgo
        """
        
        # Validar entrada
        if not text or not isinstance(text, str):
            logger.warning("Texto vacío o inválido recibido")
            return self._empty_assessment()
        
        text = text.strip()
        if len(text) < 3:
            return self._empty_assessment()
        
        history = history or []
        user_profile = user_profile or {}
        
        self._debug_log(f"🔍 Evaluando: {text[:50]}...")
        
        # Evaluar cada dimensión
        dimension_scores = {}
        for dimension in self.weights.keys():
            score = self._assess_dimension(
                dimension, text, emotional_state, history, user_profile
            )
            dimension_scores[dimension] = score
            self._debug_log(f"  {dimension}: {score:.2f}")
        
        # Calcular score ponderado
        overall_score = self._calculate_weighted_score(dimension_scores, history)
        
        # Aplicar factores agravantes contextuales
        overall_score = self._apply_contextual_factors(
            overall_score, dimension_scores, history, user_profile
        )
        
        # Determinar nivel de riesgo
        risk_level = self._determine_risk_level(overall_score, dimension_scores)
        
        self._debug_log(f"✅ Resultado final: {risk_level} (score={overall_score:.2f})")
        
        return {
            'overall_score': round(overall_score, 2),
            'risk_level': risk_level,
            'dimensions': {
                dim: {
                    'score': round(dimension_scores[dim], 2),
                    'severity': self._score_to_severity(dimension_scores[dim])
                }
                for dim in self.weights.keys()
            },
            'alert_threshold_exceeded': overall_score >= 0.55,
            'requires_escalation': overall_score >= 0.75 or dimension_scores.get("suicidalidad", 0) >= 0.45,
            'critical_dimensions': [
                d for d, s in dimension_scores.items() if s >= 0.60
            ]
        }

    def _assess_dimension(
        self,
        dimension: str,
        text: str,
        emotional_state: str,
        history: List[Dict] = None,
        user_profile: Dict = None
    ) -> float:
        """
        Evalúa una dimensión específica de riesgo de forma mejorada
        Con atención especial a suicidalidad (máxima prioridad)
        """
        
        history = history or []
        user_profile = user_profile or {}
        
        score = 0.0
        text_lower = text.lower()
        
        # 1. Detección de keywords (peso mayor, especialmente para suicidalidad)
        patterns = self.keyword_patterns.get(dimension, [])
        keyword_matches = self._detect_keywords(text_lower, patterns)
        
        # Para suicidalidad: scoring más agresivo
        if dimension == "suicidalidad":
            keyword_score = min(keyword_matches * 0.30, 0.80)  # Max 0.80 (antes 0.60)
        else:
            keyword_score = min(keyword_matches * 0.20, 0.60)
        
        score += keyword_score
        
        # 2. Análisis de frecuencia de patrones
        if keyword_matches >= 2:  # Dos o más indicadores de peligro (antes 3)
            if dimension == "suicidalidad":
                score += 0.20  # Boost aumentado para suicidalidad (antes 0.15)
            else:
                score += 0.15
        
        # 3. Indicadores emocionales
        emotion_boost = self._emotion_risk_boost(dimension, emotional_state)
        score += emotion_boost
        
        # 4. Contexto histórico y tendencias
        history_boost = self._historical_trend_boost(dimension, history)
        score += history_boost
        
        # 5. Factores de edad/perfil (si disponible)
        profile_boost = self._profile_risk_boost(dimension, user_profile)
        score += profile_boost
        
        # Normalizar a 0-1
        return min(score, 1.0)
    
    def _detect_keywords(self, text: str, patterns: List[str]) -> int:
        """Detecta keywords en el texto con búsqueda inteligente"""
        matches = 0
        for pattern in patterns:
            # Búsqueda exacta primero
            if pattern.lower() in text:
                matches += 1
            # Buscar variaciones (singularización, etc.)
            elif self._fuzzy_match(text, pattern):
                matches += 0.5  # Medio punto para coincidencias parciales
        return int(matches)
    
    def _fuzzy_match(self, text: str, pattern: str) -> bool:
        """Búsqueda fuzzy para detectar variaciones de palabras"""
        words = pattern.split()
        # Si patrón es multi-palabra, buscar cada palabra por separado
        if len(words) > 1:
            return all(word in text for word in words)
        return False
    
    def _emotion_risk_boost(self, dimension: str, emotional_state: str) -> float:
        """Amplifica score según emociones asociadas a la dimensión"""
        emotion_map = {
            "suicidalidad": {
                "deprimido": 0.25, "tristeza": 0.20, "hopelessness": 0.25,
                "soledad": 0.15, "desesesperación": 0.30
            },
            "self_harm": {
                "ira": 0.25, "disgust": 0.20, "soledad": 0.15,
                "culpa": 0.20
            },
            "isolation": {
                "tristeza": 0.20, "ansioso": 0.15, "soledad": 0.35,
                "deprimido": 0.25, "rechazado": 0.30
            },
            "hopelessness": {
                "deprimido": 0.30, "tristeza": 0.25, "soledad": 0.20,
                "desesesperación": 0.30
            },
            "sleep_disorder": {
                "ansioso": 0.20, "estresado": 0.25, "soledad": 0.10
            },
            "cognitive_decline": {
                "confuso": 0.30, "ansioso": 0.15, "deprimido": 0.10
            },
            "substance_abuse": {
                "ira": 0.15, "deprimido": 0.15, "ansioso": 0.15
            },
            "emotional_instability": {
                "ira": 0.25, "ansioso": 0.25, "soledad": 0.10,
                "pánico": 0.25
            },
        }
        
        return emotion_map.get(dimension, {}).get(emotional_state, 0.0)
    
    def _historical_trend_boost(self, dimension: str, history: List[Dict]) -> float:
        """Amplifica score si hay tendencia ascendente en historial"""
        if not history or len(history) < 2:
            return 0.0
        
        # Analizar últimos 3 registros
        recent = history[-3:]
        recent_scores = [r.get('dimensions', {}).get(dimension, {}).get('score', 0) 
                        for r in recent]
        
        # Si hay tendencia ascendente, amplificar
        if len(recent_scores) >= 2:
            trend = recent_scores[-1] - recent_scores[0]
            if trend > 0.2:  # Aumento significativo
                return 0.10
            elif trend > 0.1:
                return 0.05
        
        return 0.0
    
    def _profile_risk_boost(self, dimension: str, user_profile: Dict) -> float:
        """Amplifica score según factores de riesgo del perfil"""
        boost = 0.0
        
        # Factores de edad
        age = user_profile.get('age', 0)
        if 15 <= age <= 25:  # Grupo de alto riesgo
            if dimension in ["suicidalidad", "self_harm"]:
                boost += 0.05
        elif age > 65:  # Adultos mayores
            if dimension == "suicidalidad":
                boost += 0.08
        
        # Antecedentes relevantes
        if "suicidio_previo" in user_profile and user_profile["suicidio_previo"]:
            if dimension == "suicidalidad":
                boost += 0.15
        
        if "depression_history" in user_profile and user_profile["depression_history"]:
            if dimension in ["suicidalidad", "hopelessness"]:
                boost += 0.10
        
        return min(boost, 0.2)  # No exceder 0.2
    
    def _calculate_weighted_score(
        self,
        dimension_scores: Dict[str, float],
        history: Optional[List[Dict]] = None
    ) -> float:
        """
        Calcula score ponderado de forma limpia y transparente
        """
        history = history or []
        
        weighted_sum = 0.0
        for dim_name, score in dimension_scores.items():
            weight = self.weights.get(dim_name, 0.0)
            weighted_sum += score * weight
        
        self._debug_log(f"  [Weighted] Raw score: {weighted_sum:.3f}")
        
        # Normalizar automáticamente (debería estar entre 0-1)
        final_score = min(weighted_sum, 1.0)
        
        return final_score
    
    def _apply_contextual_factors(
        self,
        base_score: float,
        dimension_scores: Dict[str, float],
        history: Optional[List[Dict]],
        user_profile: Dict
    ) -> float:
        """
        Aplica factores contextuales para ajustar score final
        """
        history = history or []
        adjusted_score = base_score
        
        # Factor 1: Si suicidalidad es alta, elevar el score general
        suicidalidad = dimension_scores.get("suicidalidad", 0)
        if suicidalidad >= 0.60:
            # La suicidalidad debe influir fuertemente en score goblal
            adjusted_score = max(adjusted_score, suicidalidad * 0.85)
            self._debug_log(f"  [Context] Suicidalidad alta: factor aplicado")
        
        # Factor 2: Múltiples dimensiones altas (síndrome de riesgo)
        high_dims = sum(1 for s in dimension_scores.values() if s >= 0.50)
        if high_dims >= 3:
            adjusted_score = min(adjusted_score + 0.10, 1.0)
            self._debug_log(f"  [Context] {high_dims} dimensiones altas")
        
        # Factor 3: Tendencia ascendente en historial
        if history and len(history) >= 2:
            prev_scores = [h.get('overall_score', 0) for h in history[-3:]]
            if prev_scores:
                avg_trend = prev_scores[-1] - (sum(prev_scores) / len(prev_scores))
                if avg_trend > 0.15:
                    adjusted_score = min(adjusted_score + 0.05, 1.0)
                    self._debug_log(f"  [Context] Tendencia ascendente detectada")
        
        return min(adjusted_score, 1.0)
    
    def _determine_risk_level(
        self,
        overall_score: float,
        dimension_scores: Dict[str, float]
    ) -> str:
        """
        Determina nivel de riesgo basado en score y dimensiones críticas
        """
        suicidalidad = dimension_scores.get("suicidalidad", 0)
        self_harm = dimension_scores.get("self_harm", 0)
        
        # Reglas de decisión en orden de prioridad
        if overall_score >= 0.75 or suicidalidad >= 0.65:
            return "critico"
        elif overall_score >= 0.55 or self_harm >= 0.60:
            return "alto"
        elif overall_score >= 0.30:
            return "medio"
        else:
            return "bajo"
    
    def _empty_assessment(self) -> Dict:
        """Retorna evaluación vacía/default"""
        dimensions = {dim: {'score': 0.0, 'severity': 'bajo'} 
                     for dim in self.weights.keys()}
        return {
            'overall_score': 0.0,
            'risk_level': 'bajo',
            'dimensions': dimensions,
            'alert_threshold_exceeded': False,
            'requires_escalation': False,
            'critical_dimensions': []
        }
    
    def _debug_log(self, message: str):
        """Log condicional para debugging"""
        if self.enable_debug:
            logger.info(message)
            print(message)

    @staticmethod
    def _score_to_severity(score: float) -> str:
        """Convierte un score a label de severidad"""
        if score >= 0.75:
            return "crítico"
        elif score >= 0.55:
            return "alto"
        elif score >= 0.30:
            return "medio"
        else:
            return "bajo"
