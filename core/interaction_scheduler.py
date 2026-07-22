"""
Interaction Scheduler para ANA
Gestiona check-ins proactivos y scheduling inteligente de interacciones
"""

from datetime import datetime, timedelta
from typing import Dict, Tuple
from enum import Enum


class ScheduleStrategy(Enum):
    """Estrategias de scheduling basadas en riesgo"""
    CRITICAL = (30, "Cada 30 minutos")              # Riesgo crítico
    HIGH_RISK = (45, "Cada 45 minutos")             # Riesgo alto
    MEDIUM_RISK = (60, "Cada hora")                 # Riesgo medio
    LOW_RISK_DECLINING = (75, "Cada 75 minutos")    # Riesgo bajo pero declinando
    NORMAL = (90, "Cada 90 minutos")                # Normal
    STABLE = (120, "Cada 2 horas")                  # Estable
    INACTIVE = (180, "Cada 3 horas")                # Muy estable/preferencia poco activo


class InteractionScheduler:
    """
    Scheduler inteligente de interacciones
    Determina cuándo y cómo contactar al usuario
    """

    # Horarios de no-perturbación (respeta ciclo de sueño)
    SLEEP_HOURS = {
        'start': 23,    # 23:00 (11 PM)
        'end': 7        # 07:00 (7 AM)
    }

    # Horarios preferentes para interacción
    PREFERRED_HOURS = {
        'morning': (8, 12),      # 8 AM - 12 PM
        'afternoon': (14, 18),   # 2 PM - 6 PM
        'evening': (19, 22)      # 7 PM - 10 PM
    }

    def __init__(self, config: Dict = None):
        """
        Inicializa el scheduler
        
        Args:
            config: Configuración de thresholds y preferencias
        """
        self.config = config or self._default_config()

    @staticmethod
    def _default_config() -> Dict:
        """Configuración por defecto"""
        return {
            'baseline_interval_minutes': 90,
            'emergency_interval_minutes': 30,
            'max_check_ins_per_day': 10,
            'min_time_between_proactive': 15,  # Minutos
            'loneliness_factor': 0.8,  # Multiplicador si está solo
            'talkativeness_factor': 1.0,  # Multiplicador por preferencia
            'sleep_respecting': True,
            'weekday_factor': 1.0,  # Normal
            'weekend_factor': 0.8,  # Aumentar check-ins
        }

    def calculate_next_check_in(
        self,
        user_profile: Dict,
        last_analysis: Dict,
        interaction_history: list = None
    ) -> Dict:
        """
        Calcula el próximo check-in recomendado
        
        Args:
            user_profile: Perfil del usuario (loneliness, talkativeness, etc.)
            last_analysis: Último análisis realizado
            interaction_history: Historial de interacciones previas
        
        Returns:
            Dict con:
            - next_check_in_time: datetime
            - strategy: ScheduleStrategy
            - interval_minutes: int
            - reasoning: str
            - is_proactive: bool (¿debería ser ANA quien inicie?)
            - suggested_message: str
        """
        
        interaction_history = interaction_history or []
        
        # 1. Determinar estrategia basada en riesgo
        strategy = self._determine_strategy(user_profile, last_analysis, interaction_history)
        interval_minutes = strategy.value[0]
        
        # 2. Aplicar factores de ajuste
        interval_minutes = self._apply_adjustment_factors(
            interval_minutes,
            user_profile,
            last_analysis,
            interaction_history
        )
        
        # 3. Calcular tiempo próximo
        last_check_in = self._get_last_check_in_time(interaction_history)
        next_check = last_check_in + timedelta(minutes=interval_minutes)
        
        # 4. Respetar horas de sueño
        if self.config['sleep_respecting']:
            next_check = self._respect_sleep_schedule(next_check)
        
        # 5. Preferir horarios óptimos de interacción
        next_check = self._apply_preferred_hours(next_check)
        
        # 6. Determinar si debe ser proactivo o esperar respuesta
        is_proactive = self._should_be_proactive(last_analysis, interaction_history)
        
        # 7. Generar mensaje sugerido
        suggested_message = self._generate_suggested_message(
            user_profile,
            last_analysis,
            is_proactive
        )
        
        return {
            'next_check_in_time': next_check,
            'strategy': strategy.name,
            'interval_minutes': interval_minutes,
            'is_proactive': is_proactive,
            'suggested_message': suggested_message,
            'reasoning': self._generate_reasoning(strategy, user_profile, last_analysis),
            'timestamp_calculated': datetime.now()
        }

    def _determine_strategy(
        self,
        user_profile: Dict,
        last_analysis: Dict,
        interaction_history: list
    ) -> ScheduleStrategy:
        """Determina la estrategia de scheduling basada en múltiples factores"""
        
        risk_level = last_analysis.get('risk_level', 'bajo')
        trend = last_analysis.get('trend', 'stable')
        risk_score = last_analysis.get('risk_level_score', 0)
        
        # Lógica de decisión jerárquica
        
        # CRÍTICO
        if risk_score >= 0.85 or risk_level == 'critico':
            return ScheduleStrategy.CRITICAL
        
        # ALTO RIESGO
        if risk_score >= 0.65 or risk_level == 'alto':
            return ScheduleStrategy.HIGH_RISK
        
        # RIESGO MEDIO
        if risk_score >= 0.35 or risk_level == 'medio':
            return ScheduleStrategy.MEDIUM_RISK
        
        # RIESGO BAJO PERO DECLINANDO
        if trend == 'declining':
            return ScheduleStrategy.LOW_RISK_DECLINING
        
        # ESTABLE
        if trend == 'stable' and risk_score < 0.25:
            return ScheduleStrategy.STABLE
        
        # NORMAL
        return ScheduleStrategy.NORMAL

    def _apply_adjustment_factors(
        self,
        base_interval: int,
        user_profile: Dict,
        last_analysis: Dict,
        interaction_history: list
    ) -> int:
        """
        Aplica factores de ajuste al intervalo base
        """
        
        adjusted = base_interval
        
        # Factor de soledad: si está muy solo, aumentar frecuencia
        loneliness_score = user_profile.get('loneliness_score', 0)
        if loneliness_score > 0.7:
            adjusted = int(adjusted * self.config['loneliness_factor'])
        
        # Factor de preferencia de interacción (talkativeness)
        talkativeness = user_profile.get('talkativeness', 0.5)
        talkativeness_factor = 0.5 + talkativeness  # Rango 0.5-1.5
        adjusted = int(adjusted * talkativeness_factor)
        
        # Factor de día de semana
        today = datetime.now().weekday()
        if today >= 5:  # Sábado o domingo
            adjusted = int(adjusted * self.config['weekend_factor'])
        else:
            adjusted = int(adjusted * self.config['weekday_factor'])
        
        # Factor histórico: si ha habido muchas interacciones hoy, espaciar
        interactions_today = self._count_interactions_today(interaction_history)
        if interactions_today >= self.config['max_check_ins_per_day']:
            adjusted = float('inf')  # No agendar más hoy
        elif interactions_today > self.config['max_check_ins_per_day'] * 0.7:
            adjusted = int(adjusted * 1.5)  # Espaciar más
        
        # Mínimo 15 minutos, máximo 8 horas
        adjusted = max(15, min(adjusted, 480))
        
        return adjusted

    def _get_last_check_in_time(self, interaction_history: list) -> datetime:
        """Obtiene la hora del último check-in o ahora si no hay historial"""
        
        if not interaction_history:
            return datetime.now()
        
        # Asumir que último elemento es el más reciente
        last_interaction = interaction_history[-1]
        
        if isinstance(last_interaction, dict):
            timestamp = last_interaction.get('createdAt') or last_interaction.get('timestamp')
            if timestamp:
                if isinstance(timestamp, str):
                    try:
                        return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    except:
                        return datetime.now()
                return timestamp
        
        return datetime.now()

    def _respect_sleep_schedule(self, scheduled_time: datetime) -> datetime:
        """
        Ajusta el tiempo programado para respetar horas de sueño
        No enviar notificaciones entre 23:00 y 07:00
        """
        
        hour = scheduled_time.hour
        start_sleep = self.SLEEP_HOURS['start']
        end_sleep = self.SLEEP_HOURS['end']
        
        # Verificar si cae en horario de sueño
        if hour >= start_sleep or hour < end_sleep:
            # Posponer al próximo horario despierto (8 AM)
            next_scheduled = scheduled_time.replace(hour=end_sleep + 1, minute=0, second=0)
            
            # Si ya pasó el próximo 8 AM de hoy, ir al de mañana
            if next_scheduled <= scheduled_time:
                next_scheduled += timedelta(days=1)
            
            return next_scheduled
        
        return scheduled_time

    def _apply_preferred_hours(self, scheduled_time: datetime) -> datetime:
        """
        Intenta ajustar el tiempo a horarios preferentes de interacción
        Mañana > Tarde > Noche > Noche tarde
        """
        
        hour = scheduled_time.hour
        
        # Si ya está en horario preferente, mantener
        for period, (start, end) in self.PREFERRED_HOURS.items():
            if start <= hour < end:
                return scheduled_time
        
        # De lo contrario, ajustar al próximo horario preferente
        if hour < self.PREFERRED_HOURS['morning'][0]:  # Antes de 8 AM
            return scheduled_time.replace(hour=self.PREFERRED_HOURS['morning'][0], minute=0)
        elif hour < self.PREFERRED_HOURS['afternoon'][0]:  # 8-14
            return scheduled_time.replace(hour=self.PREFERRED_HOURS['afternoon'][0], minute=0)
        elif hour < self.PREFERRED_HOURS['evening'][0]:  # 14-19
            return scheduled_time.replace(hour=self.PREFERRED_HOURS['evening'][0], minute=0)
        else:  # Después de 22
            # Al día siguiente, mañana
            return (scheduled_time + timedelta(days=1)).replace(hour=8, minute=0)

    def _should_be_proactive(
        self,
        last_analysis: Dict,
        interaction_history: list
    ) -> bool:
        """
        Determina si ANA debe iniciar la interacción (proactiva) o esperar
        """
        
        # La interacción debería ser proactiva si:
        # 1. Hay riesgo elevado
        # 2. Hay patrones de declive
        # 3. Hay inactividad prolongada
        
        risk_level = last_analysis.get('risk_level', 'bajo')
        trend = last_analysis.get('trend', 'stable')
        
        # Riesgo alto → siempre proactivo
        if risk_level in ['alto', 'critico']:
            return True
        
        # Tendencia declinante → proactivo
        if trend == 'declining':
            return True
        
        # Inactividad > 2 horas → proactivo
        if interaction_history:
            hours_inactive = self._hours_since_last_interaction(interaction_history)
            if hours_inactive > 2:
                return True
        
        # Caso contrario: esperar que el usuario inicie
        return False

    def _hours_since_last_interaction(self, interaction_history: list) -> float:
        """Calcula horas desde la última interacción"""
        
        if not interaction_history:
            return 0.0
        
        last_time = self._get_last_check_in_time(interaction_history)
        hours = (datetime.now() - last_time).total_seconds() / 3600
        
        return hours

    def _count_interactions_today(self, interaction_history: list) -> int:
        """Cuenta interacciones desde las 00:00 de hoy"""
        
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        count = 0
        for interaction in interaction_history:
            if isinstance(interaction, dict):
                timestamp = interaction.get('createdAt') or interaction.get('timestamp')
                if timestamp:
                    if isinstance(timestamp, str):
                        try:
                            interaction_time = datetime.fromisoformat(
                                timestamp.replace('Z', '+00:00')
                            )
                        except:
                            continue
                    else:
                        interaction_time = timestamp
                    
                    if interaction_time >= today_start:
                        count += 1
        
        return count

    def _generate_suggested_message(
        self,
        user_profile: Dict,
        last_analysis: Dict,
        is_proactive: bool
    ) -> str:
        """
        Genera un mensaje sugerido para el check-in
        """
        
        name = user_profile.get('name', 'amigo')
        emotional_state = last_analysis.get('emotional_state', 'neutral')
        formality = user_profile.get('formality', 0.5)
        
        # Seleccionar nivel de formalidad
        greeting = "Hola" if formality < 0.5 else "Estimado/a"
        
        # Mensajes personalizados por estado emocional y contexto
        if not is_proactive:
            # El usuario puede iniciar - mensaje pasivo
            base_message = f"{greeting} {name}, estoy aquí si necesitas hablar sobre cómo te sientes."
        else:
            # ANA inicia - mensaje empático
            messages_by_state = {
                'deprimido': f"{greeting} {name}, he notado que te sientes algo triste. ¿Te gustaría conversar?",
                'ansioso': f"{greeting} {name}, veo que estás un poco ansioso. Puedo ayudarte a calmarte.",
                'estresado': f"{greeting} {name}, ¿cómo va tu día? Quería saber cómo te sientes.",
                'tristeza': f"{greeting} {name}, parece que algo te molesta. Estoy aquí para escucharte.",
                'neutral': f"{greeting} {name}, ¿cómo estás en este momento?",
                'alegria': f"{greeting} {name}, ¡me alegra que estés bien! ¿Qué buenas noticias tienes?"
            }
            
            base_message = messages_by_state.get(
                emotional_state,
                f"{greeting} {name}, ¿cómo te sientes ahora?"
            )
        
        return base_message

    def _generate_reasoning(
        self,
        strategy: ScheduleStrategy,
        user_profile: Dict,
        last_analysis: Dict
    ) -> str:
        """Genera una explicación del scheduling"""
        
        reasons = []
        
        risk_level = last_analysis.get('risk_level', 'bajo')
        trend = last_analysis.get('trend', 'stable')
        
        if risk_level == 'critico':
            reasons.append("Riesgo clínico crítico - contacto inmediato requerido")
        elif risk_level == 'alto':
            reasons.append("Riesgo emocional elevado - monitoreo cercano")
        elif risk_level == 'medio':
            reasons.append("Riesgo moderado - seguimiento regular")
        
        if trend == 'declining':
            reasons.append("Patrón de declive emocional detectado")
        elif trend == 'improving':
            reasons.append("Tendencia positiva en estado emocional")
        
        if user_profile.get('loneliness_score', 0) > 0.7:
            reasons.append("Soledad detectada - aumentar frecuencia de contacto")
        
        return " | ".join(reasons) if reasons else "Interacción de rutina"
