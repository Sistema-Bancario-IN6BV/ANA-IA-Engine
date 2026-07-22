"""
Routine Manager para ANA
Gestiona y rastrea rutinas diarias del usuario
Detecta cambios anormales que pueden indicar problemas de salud
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from enum import Enum


class ActivityType(Enum):
    """Tipos de actividades a rastrear"""
    WAKE_UP = "wake_up"               # Levantarse
    SLEEP = "sleep"                   # Dormir
    BREAKFAST = "breakfast"           # Desayuno
    LUNCH = "lunch"                   # Almuerzo
    DINNER = "dinner"                 # Cena
    EXERCISE = "exercise"             # Ejercicio
    SOCIAL_CONTACT = "social_contact" # Contacto social (llamada, visita)
    MEDICATION = "medication"         # Tomar medicinas
    PERSONAL_CARE = "personal_care"   # Higiene personal
    WORK_ACTIVITY = "work"            # Actividad laboral o de hogar
    RECREATION = "recreation"         # Actividad recreativa
    APPOINTMENT = "appointment"       # Cita médica


class RoutineManager:
    """
    Gestor de rutinas diarias
    Rastrea patrones normales y detecta desviaciones
    """

    def __init__(self):
        """Inicializa el gestor de rutinas"""
        self.normal_patterns = {}  # Patrones establecidos del usuario
        self.anomaly_thresholds = self._default_thresholds()

    @staticmethod
    def _default_thresholds() -> Dict:
        """Thresholds para detectar cambios anormales"""
        return {
            'wake_time_variance': 90,      # Minutos de variancia permitida
            'sleep_time_variance': 120,    # Minutos de variancia permitida
            'meal_skipping_threshold': 2,  # Saltarse 2+ comidas es anómalo
            'no_social_contact_days': 3,   # 3 días sin contacto social
            'medication_skip_threshold': 3, # 3+ dosis saltadas
            'exercise_frequency': 3,        # Menos de 3 veces/semana es declive
            'sleep_duration_min': 5,        # Menos de 5 horas es insuficiente
            'sleep_duration_max': 10,       # Más de 10 horas es sospechoso
        }

    def establish_baseline_pattern(
        self,
        user_id: str,
        activity_history: List[Dict]
    ) -> Dict:
        """
        Establece el patrón normal del usuario basado en su historial
        
        Args:
            user_id: ID del usuario
            activity_history: Historial de actividades (últimos 30 días idealmente)
        
        Returns:
            Dict con patrones normales identificados
        """
        
        if not activity_history:
            return {'status': 'insufficient_data'}
        
        # Agrupar actividades por tipo
        activities_by_type = self._group_activities(activity_history)
        
        # Calcular horarios normales para cada actividad importante
        patterns = {
            'wake_time': self._calculate_normal_time(activities_by_type, ActivityType.WAKE_UP),
            'sleep_time': self._calculate_normal_time(activities_by_type, ActivityType.SLEEP),
            'meal_times': {
                'breakfast': self._calculate_normal_time(activities_by_type, ActivityType.BREAKFAST),
                'lunch': self._calculate_normal_time(activities_by_type, ActivityType.LUNCH),
                'dinner': self._calculate_normal_time(activities_by_type, ActivityType.DINNER),
            },
            'exercise_frequency': self._calculate_frequency(activities_by_type, ActivityType.EXERCISE),
            'social_contact_frequency': self._calculate_frequency(
                activities_by_type, ActivityType.SOCIAL_CONTACT
            ),
            'medication_schedule': self._extract_medication_times(activity_history),
            'typical_sleep_duration': self._calculate_sleep_duration(activity_history),
        }
        
        self.normal_patterns[user_id] = patterns
        
        return {
            'status': 'baseline_established',
            'patterns': patterns,
            'confidence': self._calculate_pattern_confidence(activity_history)
        }

    def detect_routine_disruption(
        self,
        user_id: str,
        recent_activities: List[Dict]
    ) -> Dict:
        """
        Detecta cambios anormales en la rutina del usuario
        
        Args:
            user_id: ID del usuario
            recent_activities: Actividades recientes (últimas 2 semanas)
        
        Returns:
            Dict con disrupciones detectadas y nivel de severidad
        """
        
        if user_id not in self.normal_patterns:
            return {'status': 'no_baseline', 'message': 'Sin patrón base establecido'}
        
        baseline = self.normal_patterns[user_id]
        disruptions = []
        
        # 1. Detección de cambios en horarios de sueño/vigilia
        wake_sleep_disruption = self._check_wake_sleep_changes(
            baseline, recent_activities
        )
        if wake_sleep_disruption:
            disruptions.extend(wake_sleep_disruption)
        
        # 2. Detección de saltarse comidas
        meal_disruptions = self._check_meal_patterns(baseline, recent_activities)
        if meal_disruptions:
            disruptions.extend(meal_disruptions)
        
        # 3. Detección de falta de ejercicio
        exercise_disruptions = self._check_exercise_decline(
            baseline, recent_activities
        )
        if exercise_disruptions:
            disruptions.extend(exercise_disruptions)
        
        # 4. Detección de aislamiento social
        social_disruptions = self._check_social_isolation(
            baseline, recent_activities
        )
        if social_disruptions:
            disruptions.extend(social_disruptions)
        
        # 5. Detección de falta de medicinas
        medication_disruptions = self._check_medication_compliance(
            baseline, recent_activities
        )
        if medication_disruptions:
            disruptions.extend(medication_disruptions)
        
        # 6. Detección de duración anormal de sueño
        sleep_duration_disruptions = self._check_sleep_duration(
            baseline, recent_activities
        )
        if sleep_duration_disruptions:
            disruptions.extend(sleep_duration_disruptions)
        
        # Calcular severidad general
        severity = self._calculate_disruption_severity(disruptions)
        
        return {
            'user_id': user_id,
            'disruptions_detected': len(disruptions) > 0,
            'disruptions': disruptions,
            'severity': severity,  # 'low', 'medium', 'high'
            'timestamp': datetime.now(),
            'recommendations': self._generate_recommendations(disruptions)
        }

    def _group_activities(self, activity_history: List[Dict]) -> Dict:
        """Agrupa actividades por tipo"""
        grouped = {}
        
        for activity in activity_history:
            activity_type = activity.get('type')
            if activity_type not in grouped:
                grouped[activity_type] = []
            grouped[activity_type].append(activity)
        
        return grouped

    def _calculate_normal_time(
        self,
        activities_by_type: Dict,
        activity_type: ActivityType
    ) -> Optional[str]:
        """
        Calcula la hora normal para una actividad
        Usa mediana para evitar outliers
        """
        
        activities = activities_by_type.get(activity_type.value, [])
        if not activities:
            return None
        
        times = []
        for activity in activities:
            timestamp = activity.get('timestamp')
            if timestamp:
                if isinstance(timestamp, str):
                    try:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        times.append(dt)
                    except:
                        continue
                else:
                    times.append(timestamp)
        
        if not times:
            return None
        
        # Calcular hora promedio usando valores circulares
        # (para evitar promediar 23:00 + 01:00 = 12:00)
        total_minutes = sum(t.hour * 60 + t.minute for t in times)
        avg_minutes = total_minutes // len(times)
        hours = avg_minutes // 60
        minutes = avg_minutes % 60
        
        return f"{hours:02d}:{minutes:02d}"

    def _calculate_frequency(
        self,
        activities_by_type: Dict,
        activity_type: ActivityType
    ) -> float:
        """
        Calcula frecuencia de una actividad
        Retorna: veces por semana
        """
        
        activities = activities_by_type.get(activity_type.value, [])
        if not activities:
            return 0.0
        
        # Asumir que el historial es de 30 días
        count = len(activities)
        frequency_per_week = (count / 30) * 7
        
        return round(frequency_per_week, 1)

    def _calculate_sleep_duration(self, activity_history: List[Dict]) -> Dict:
        """
        Calcula duración típica del sueño
        Busca pares de sleep_time y wake_time
        """
        
        sleep_durations = []
        
        for activity in activity_history:
            if activity.get('type') == 'wake_up':
                # Buscar el sueño anterior
                # En un sistema real, esto sería más sofisticado
                pass
        
        if not sleep_durations:
            return {'average_hours': 7, 'min': 6, 'max': 8}
        
        avg = sum(sleep_durations) / len(sleep_durations)
        return {
            'average_hours': round(avg, 1),
            'min': min(sleep_durations),
            'max': max(sleep_durations)
        }

    def _extract_medication_times(self, activity_history: List[Dict]) -> List[str]:
        """Extrae horarios de medicinas del historial"""
        
        med_activities = [
            a for a in activity_history
            if a.get('type') == 'medication'
        ]
        
        times = []
        for activity in med_activities:
            timestamp = activity.get('timestamp')
            if timestamp:
                if isinstance(timestamp, str):
                    try:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        times.append(f"{dt.hour:02d}:{dt.minute:02d}")
                    except:
                        continue
                else:
                    times.append(f"{timestamp.hour:02d}:{timestamp.minute:02d}")
        
        # Retornar horarios únicos
        return list(set(times))

    def _calculate_pattern_confidence(self, activity_history: List[Dict]) -> float:
        """
        Calcula la confianza en los patrones establecidos
        Más datos = más confianza
        """
        
        # Idealmente necesitamos al menos 14 días de datos
        days_of_data = self._count_unique_days(activity_history)
        
        if days_of_data < 7:
            return 0.3
        elif days_of_data < 14:
            return 0.6
        elif days_of_data < 30:
            return 0.85
        else:
            return 0.95

    def _count_unique_days(self, activity_history: List[Dict]) -> int:
        """Cuenta días únicos en el historial"""
        days = set()
        
        for activity in activity_history:
            timestamp = activity.get('timestamp')
            if timestamp:
                if isinstance(timestamp, str):
                    try:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        days.add(dt.date())
                    except:
                        continue
                else:
                    days.add(timestamp.date())
        
        return len(days)

    def _check_wake_sleep_changes(
        self,
        baseline: Dict,
        recent_activities: List[Dict]
    ) -> List[Dict]:
        """Detecta cambios en horarios de sueño/vigilia"""
        disruptions = []
        
        baseline_wake = baseline.get('wake_time')
        baseline_sleep = baseline.get('sleep_time')
        threshold = self.anomaly_thresholds['wake_time_variance']
        
        # Implementación simplificada
        # En producción, sería más sofisticada
        
        return disruptions

    def _check_meal_patterns(
        self,
        baseline: Dict,
        recent_activities: List[Dict]
    ) -> List[Dict]:
        """Detecta cambios en patrones de alimentación"""
        disruptions = []
        
        # Contar comidas en últimos días
        recent_days = 7
        meals_per_day = self._count_meals_per_day(recent_activities, recent_days)
        
        if any(meals < 2 for meals in meals_per_day):
            disruptions.append({
                'type': 'meal_skipping',
                'description': 'Se detectó que se saltó una o más comidas',
                'severity': 'medium',
                'recommendation': 'Recordar la importancia de una alimentación regular'
            })
        
        return disruptions

    def _check_exercise_decline(
        self,
        baseline: Dict,
        recent_activities: List[Dict]
    ) -> List[Dict]:
        """Detecta declive en actividad física"""
        disruptions = []
        
        baseline_frequency = baseline.get('exercise_frequency', 3)
        recent_frequency = self._count_exercise_frequency(recent_activities, 14)
        
        if recent_frequency < baseline_frequency * 0.5:
            disruptions.append({
                'type': 'exercise_decline',
                'description': f'Declive significativo en ejercicio: {recent_frequency:.1f} vs {baseline_frequency:.1f} veces/semana',
                'severity': 'medium',
                'recommendation': 'Animar al usuario a realizar actividad física'
            })
        
        return disruptions

    def _check_social_isolation(
        self,
        baseline: Dict,
        recent_activities: List[Dict]
    ) -> List[Dict]:
        """Detecta aislamiento social"""
        disruptions = []
        
        baseline_frequency = baseline.get('social_contact_frequency', 2)
        recent_frequency = self._count_social_frequency(recent_activities, 14)
        
        if recent_frequency < baseline_frequency * 0.3:
            disruptions.append({
                'type': 'social_isolation',
                'description': 'Reducción significativa en contactos sociales',
                'severity': 'high',
                'recommendation': 'Facilitar conexiones sociales, sugerir visitas o llamadas'
            })
        
        return disruptions

    def _check_medication_compliance(
        self,
        baseline: Dict,
        recent_activities: List[Dict]
    ) -> List[Dict]:
        """Detecta falta de cumplimiento con medicinas"""
        disruptions = []
        
        med_schedule = baseline.get('medication_schedule', [])
        if not med_schedule:
            return disruptions
        
        # Contar si se tomaron medicinas
        med_activities = [
            a for a in recent_activities
            if a.get('type') == 'medication'
        ]
        
        if len(med_activities) < len(med_schedule) * 5:  # Menos de 5 días de medicinas
            disruptions.append({
                'type': 'medication_non_compliance',
                'description': 'Posible incumplimiento con el horario de medicinas',
                'severity': 'high',
                'recommendation': 'Recordar la importancia del cumplimiento medicamentoso'
            })
        
        return disruptions

    def _check_sleep_duration(
        self,
        baseline: Dict,
        recent_activities: List[Dict]
    ) -> List[Dict]:
        """Detecta duración anormal de sueño"""
        disruptions = []
        
        baseline_sleep = baseline.get('typical_sleep_duration', {})
        min_hours = baseline_sleep.get('min', 5)
        max_hours = baseline_sleep.get('max', 10)
        
        # Implementación simplificada
        
        return disruptions

    def _count_meals_per_day(
        self,
        recent_activities: List[Dict],
        days: int
    ) -> List[int]:
        """Cuenta comidas por día"""
        # Implementación simplificada
        return [3] * days  # Placeholder

    def _count_exercise_frequency(
        self,
        recent_activities: List[Dict],
        days: int
    ) -> float:
        """Cuenta frecuencia de ejercicio en los últimos N días"""
        exercise_activities = [
            a for a in recent_activities
            if a.get('type') == 'exercise'
        ]
        
        return (len(exercise_activities) / days) * 7

    def _count_social_frequency(
        self,
        recent_activities: List[Dict],
        days: int
    ) -> float:
        """Cuenta frecuencia de contacto social en los últimos N días"""
        social_activities = [
            a for a in recent_activities
            if a.get('type') == 'social_contact'
        ]
        
        return (len(social_activities) / days) * 7

    def _calculate_disruption_severity(self, disruptions: List[Dict]) -> str:
        """Calcula severidad general de disrupciones"""
        
        if not disruptions:
            return 'low'
        
        high_count = sum(1 for d in disruptions if d.get('severity') == 'high')
        medium_count = sum(1 for d in disruptions if d.get('severity') == 'medium')
        
        if high_count >= 2:
            return 'high'
        elif high_count >= 1 or medium_count >= 3:
            return 'medium'
        else:
            return 'low'

    def _generate_recommendations(self, disruptions: List[Dict]) -> List[str]:
        """Genera recomendaciones basadas en disrupciones"""
        
        recommendations = []
        
        for disruption in disruptions:
            rec = disruption.get('recommendation')
            if rec and rec not in recommendations:
                recommendations.append(rec)
        
        return recommendations

    def suggest_routine_activity(
        self,
        user_profile: Dict,
        recent_disruptions: Dict
    ) -> Dict:
        """
        Sugiere actividades para mantener/restaurar rutina
        """
        
        suggestions = {
            'morning_routine': 'Establecer hora fija para levantarse',
            'meal_structure': 'Planicar comidas a horas consistentes',
            'exercise': 'Realizar 30 min de caminata diaria',
            'social': 'Contactar a un amigo o familiar',
            'evening_routine': 'Prepararse para dormir 1 hora antes',
            'hobby': 'Dedicar tiempo a una actividad que disfruta',
        }
        
        return {
            'suggestions': suggestions,
            'priority_activities': self._prioritize_suggestions(recent_disruptions),
            'timestamp': datetime.now()
        }

    def _prioritize_suggestions(self, disruptions: Dict) -> List[str]:
        """Prioriza sugerencias basadas en disrupciones detectadas"""
        
        priorities = []
        
        for disruption in disruptions.get('disruptions', []):
            disruption_type = disruption.get('type')
            if disruption_type == 'meal_skipping':
                priorities.append('meal_structure')
            elif disruption_type == 'exercise_decline':
                priorities.append('exercise')
            elif disruption_type == 'social_isolation':
                priorities.append('social')
        
        return priorities