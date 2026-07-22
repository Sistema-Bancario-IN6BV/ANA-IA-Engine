"""
Decision Engine para ANA
Determina qué acción tomar basada en el análisis psicológico del usuario
"""

from enum import Enum
from typing import Dict, List, Tuple
from datetime import datetime, timedelta


class ActionType(Enum):
    """Tipos de acciones que ANA puede tomar"""
    RESPOND_EMPATHIC = "respond_empathic"           # Respuesta estándar empática
    ESCALATE_TO_CAREGIVER = "escalate_to_caregiver" # Notificar al cuidador
    SUGGEST_EXERCISE = "suggest_exercise"           # Proponer ejercicio cognitivo
    REQUEST_PROFESSIONAL_HELP = "request_help"     # Sugerir ayuda profesional
    MONITOR_INTENSIVELY = "monitor_intensively"     # Aumentar monitoreo
    PROVIDE_RESOURCES = "provide_resources"         # Compartir recursos
    SCHEDULE_CHECK_IN = "schedule_check_in"         # Programar check-in próximo


class DecisionEngine:
    """
    Motor de decisiones para determinar acciones basadas en análisis psicológico
    """

    def __init__(self, config: Dict = None):
        """
        Inicializa el motor de decisiones con configuración de thresholds
        
        Args:
            config: Diccionario con thresholds y pesos de decisión
        """
        self.config = config or self._default_config()

    @staticmethod
    def _default_config() -> Dict:
        """Configuración por defecto de thresholds de decisión"""
        return {
            'critical_risk_threshold': 0.75,      # Score de riesgo crítico
            'high_risk_threshold': 0.60,          # Score de riesgo alto
            'decline_threshold': 0.65,            # Threshold para declive emocional
            'loneliness_alert': 0.70,             # Score de soledad que requiere alerta
            'inactivity_hours': 2,                # Horas de inactividad para alerta
            'declining_trend_window': 5,          # Últimas N muestras para detectar declive
            'improvement_window': 3,              # Últimas N muestras para detectar mejora
        }

    def determine_action(
        self,
        current_analysis: Dict,
        user_history: List[Dict],
        user_profile: Dict
    ) -> Tuple[ActionType, Dict]:
        """
        Determina la acción a tomar basada en análisis y contexto del usuario
        
        Args:
            current_analysis: Análisis actual con emociones, risk_level, etc.
            user_history: Historial de análisis previos [últimos 20]
            user_profile: Perfil del usuario con scores de riesgo
        
        Returns:
            Tuple[ActionType, Dict]: (acción a tomar, detalles de recomendación)
        """
        
        # 1. Evaluar riesgo clínico
        risk_score = self._calculate_clinical_risk_score(current_analysis, user_history)
        
        # 2. Detectar patrones de declive
        is_declining = self._detect_emotional_decline(user_history)
        
        # 3. Evaluar aislamiento social
        loneliness_score = user_profile.get('loneliness_score', 0)
        is_isolated = loneliness_score > self.config['loneliness_alert']
        
        # 4. Evaluar actividad reciente
        hours_inactive = self._calculate_inactivity_hours(user_history)
        is_inactive = hours_inactive > self.config['inactivity_hours']
        
        # 5. Lógica de decisión jerárquica
        
        # CRÍTICO: Riesgo muy alto (ideación suicida, automutilación)
        if risk_score >= self.config['critical_risk_threshold']:
            return ActionType.ESCALATE_TO_CAREGIVER, {
                'reason': 'Riesgo crítico detectado',
                'risk_score': risk_score,
                'recommended_action': 'Contacto inmediato con cuidador/profesional',
                'severity': 'CRITICAL'
            }
        
        # ALTO: Riesgo significativo + declive
        if risk_score >= self.config['high_risk_threshold']:
            if is_isolated:
                return ActionType.ESCALATE_TO_CAREGIVER, {
                    'reason': 'Riesgo alto + aislamiento social',
                    'risk_score': risk_score,
                    'loneliness_score': loneliness_score,
                    'recommended_action': 'Notificar al cuidador para acompañamiento',
                    'severity': 'HIGH'
                }
            else:
                return ActionType.MONITOR_INTENSIVELY, {
                    'reason': 'Riesgo alto detectado',
                    'risk_score': risk_score,
                    'next_check_in_minutes': 30,
                    'recommended_action': 'Aumentar frecuencia de check-ins',
                    'severity': 'HIGH'
                }
        
        # DECLIVE EMOCIONAL: Sin riesgo crítico pero empeorando
        if is_declining and not is_isolated:
            return ActionType.MONITOR_INTENSIVELY, {
                'reason': 'Tendencia emocional declinante',
                'trend': 'declining',
                'next_check_in_minutes': 60,
                'recommended_action': 'Monitoreo cercano',
                'suggestion': 'Proponer actividad reconfortante',
                'severity': 'MEDIUM'
            }
        
        # DECLIVE + AISLAMIENTO: Combinación peligrosa
        if is_declining and is_isolated:
            return ActionType.SUGGEST_EXERCISE, {
                'reason': 'Declive emocional + aislamiento detectados',
                'trend': 'declining',
                'loneliness_score': loneliness_score,
                'recommended_action': 'Proponer ejercicio cognitivo de interacción',
                'severity': 'MEDIUM'
            }
        
        # INACTIVIDAD: No hay actividad reciente
        if is_inactive:
            return ActionType.SCHEDULE_CHECK_IN, {
                'reason': f'Inactividad prolongada ({hours_inactive} horas)',
                'hours_inactive': hours_inactive,
                'recommended_action': 'Check-in amistoso para estimular interacción',
                'severity': 'MEDIUM'
            }
        
        # AISLAMIENTO: Usuario sin interacciones sociales suficientes
        if is_isolated:
            return ActionType.PROVIDE_RESOURCES, {
                'reason': 'Soledad detectada',
                'loneliness_score': loneliness_score,
                'recommended_action': 'Compartir recursos de apoyo social',
                'resources': ['números de crisis', 'grupos de apoyo local', 'actividades comunitarias'],
                'severity': 'MEDIUM'
            }
        
        # ESTADO DEPRESIVO CONSISTENTE
        if current_analysis.get('emotional_state') == 'deprimido':
            return ActionType.REQUEST_PROFESSIONAL_HELP, {
                'reason': 'Usuario reporta estado depresivo',
                'emotional_state': 'deprimido',
                'recommended_action': 'Sugerir consulta profesional',
                'severity': 'MEDIUM'
            }
        
        # NORMAL: Respuesta empática estándar
        return ActionType.RESPOND_EMPATHIC, {
            'reason': 'Análisis dentro de parámetros normales',
            'emotional_state': current_analysis.get('emotional_state'),
            'recommended_action': 'Responder empáticamente, mantener check-ins regulares',
            'next_check_in_minutes': 90,
            'severity': 'LOW'
        }

    def _calculate_clinical_risk_score(
        self,
        current_analysis: Dict,
        user_history: List[Dict]
    ) -> float:
        """
        Calcula un score de riesgo clínico (0-1)
        
        Factores:
        - Keywords de riesgo (ideación suicida, automutilación): +0.5-0.8
        - Risk level del análisis: bajo=0, medio=0.3, alto=0.6
        - Emociones negativas intensas: 0.2-0.4
        - Patrón de declive: +0.1-0.2
        """
        
        score = 0.0
        
        # 1. Detección de keywords de riesgo crítico
        critical_keywords = [
            'morir', 'suicida', 'matarme', 'no vale la pena',
            'mejor si no estuviera', 'cortarme', 'hacerme daño',
            'consumo', 'droga', 'alcohol'
        ]
        
        text = current_analysis.get('original_text', '').lower()
        if any(keyword in text for keyword in critical_keywords):
            score += 0.50  # Riesgo significativo solo por keywords
        
        # 2. Risk level del análisis
        risk_level = current_analysis.get('risk_level', 'bajo')
        risk_scores = {'bajo': 0.0, 'medio': 0.25, 'alto': 0.50}
        score += risk_scores.get(risk_level, 0.0)
        
        # 3. Intensidad emocional negativa
        negative_emotions = {
            'tristeza': 0.15, 'miedo': 0.15, 'ira': 0.10,
            'disgust': 0.10, 'estresado': 0.10, 'deprimido': 0.20,
            'ansioso': 0.15
        }
        emotion = current_analysis.get('emotional_state', 'neutral')
        score += negative_emotions.get(emotion, 0.0)
        
        # 4. Patrón de declive en historial
        if self._detect_emotional_decline(user_history):
            score += 0.10
        
        # Normalizar a 0-1
        return min(score, 1.0)

    def _detect_emotional_decline(self, user_history: List[Dict]) -> bool:
        """
        Detecta si el usuario está en declive emocional
        
        Método: Comparar promedio de últimas N muestras vs muestras anteriores
        """
        if len(user_history) < self.config['declining_trend_window']:
            return False
        
        window = self.config['declining_trend_window']
        
        # Emociones mapeadas a valores numéricos
        emotion_values = {
            'alegria': 2, 'sorpresa': 1.5,
            'neutral': 0,
            'miedo': -1.5, 'disgust': -1.5, 'ira': -1.5, 'ansioso': -1,
            'estresado': -1, 'tristeza': -2, 'deprimido': -2.5
        }
        
        # Obtener últimas N muestras
        recent = user_history[-window:]
        
        # Calcular valor promedio de emociones recientes
        recent_values = [
            emotion_values.get(a.get('emotional_state', 'neutral'), 0)
            for a in recent
        ]
        recent_avg = sum(recent_values) / len(recent_values) if recent_values else 0
        
        # Comparar con período anterior (si existe)
        if len(user_history) > window * 2:
            previous = user_history[-(window*2) : -window]
            previous_values = [
                emotion_values.get(a.get('emotional_state', 'neutral'), 0)
                for a in previous
            ]
            previous_avg = sum(previous_values) / len(previous_values) if previous_values else 0
            
            # Declive si el promedio reciente es significativamente menor
            decline_threshold = self.config['decline_threshold'] / 100  # Porcentaje
            return recent_avg < (previous_avg * 0.8)  # 20% de decline
        
        # Si no hay histórico suficiente, no determinar declive
        return False

    def _calculate_inactivity_hours(self, user_history: List[Dict]) -> float:
        """
        Calcula horas desde la última actividad del usuario
        """
        if not user_history:
            return float('inf')  # Nunca han usado el sistema
        
        last_activity = user_history[-1].get('createdAt')
        if not last_activity:
            return 0
        
        # Asumir que last_activity es un timestamp
        if isinstance(last_activity, str):
            try:
                last_activity = datetime.fromisoformat(last_activity.replace('Z', '+00:00'))
            except:
                return 0
        
        hours_since = (datetime.now(last_activity.tzinfo) - last_activity).total_seconds() / 3600
        return hours_since

    def calculate_next_check_in(
        self,
        action: ActionType,
        user_profile: Dict,
        last_check_in: datetime = None
    ) -> datetime:
        """
        Calcula cuándo debe ser el próximo check-in basado en la acción
        
        Returns:
            datetime: Timestamp del próximo check-in recomendado
        """
        
        if last_check_in is None:
            last_check_in = datetime.now()
        
        # Intervals por tipo de acción
        intervals = {
            ActionType.RESPOND_EMPATHIC: 90,              # 90 minutos
            ActionType.ESCALATE_TO_CAREGIVER: 30,         # 30 minutos (urgente)
            ActionType.SUGGEST_EXERCISE: 60,              # 1 hora
            ActionType.REQUEST_PROFESSIONAL_HELP: 120,    # 2 horas
            ActionType.MONITOR_INTENSIVELY: 30,           # 30 minutos
            ActionType.PROVIDE_RESOURCES: 180,            # 3 horas
            ActionType.SCHEDULE_CHECK_IN: 45,             # 45 minutos
        }
        
        minutes = intervals.get(action, 90)
        
        # Ajustar por loneliness (aumentar frecuencia)
        if user_profile.get('loneliness_score', 0) > 0.7:
            minutes = int(minutes * 0.7)  # Reducir en 30%
        
        # Ajustar por preferencia de talkativeness
        talkativeness = user_profile.get('talkativeness', 0.5)
        if talkativeness < 0.3:
            minutes = int(minutes * 1.3)  # Espaciar más
        
        # No enviar entre las 23:00 y 07:00
        next_check = last_check_in + timedelta(minutes=minutes)
        hour = next_check.hour
        
        if 23 <= hour or hour < 7:
            # Posponer hasta las 8:00
            next_check = next_check.replace(hour=8, minute=0, second=0)
            if next_check <= last_check_in:
                next_check += timedelta(days=1)
        
        return next_check
