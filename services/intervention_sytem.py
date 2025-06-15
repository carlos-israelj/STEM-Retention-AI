from models import Student, Mentor, Intervention, MentorMatch, db
from services.support_services import PerplexityService
from datetime import datetime

class InterventionSystem:
    """Sistema de gestión de intervenciones para estudiantes en riesgo"""
    
    @staticmethod
    def trigger_intervention(student_id, risk_score):
        """Activar intervención basada en el nivel de riesgo"""
        try:
            student = Student.query.get(student_id)
            if not student:
                return False
            
            level = InterventionSystem.determine_intervention_level(risk_score)
            
            # Solo crear nueva intervención si el nivel cambió
            if student.intervention_level != level:
                student.intervention_level = level
                
                if level == 1:
                    InterventionSystem.level_1_intervention(student)
                elif level == 2:
                    InterventionSystem.level_2_intervention(student)
                elif level == 3:
                    InterventionSystem.level_3_intervention(student)
                
                db.session.commit()
                print(f"✅ Intervención nivel {level} activada para {student.name}")
                return True
            
            return False
        except Exception as e:
            print(f"Error activando intervención: {e}")
            return False
    
    @staticmethod
    def determine_intervention_level(risk_score):
        """Determinar nivel de intervención según score de riesgo"""
        if risk_score < 0.3:
            return 0  # Sin intervención
        elif risk_score < 0.6:
            return 1  # Recursos automáticos
        elif risk_score < 0.8:
            return 2  # Conexión con mentora
        else:
            return 3  # Alerta a consejeros
    
    @staticmethod
    def level_1_intervention(student):
        """Intervención Nivel 1: Recursos automáticos y contenido motivacional"""
        try:
            risk_factors = f"Programa: {student.program}, Semestre: {student.semester}, Factores: disminución participación oral, indicadores síndrome del impostor"
            content = PerplexityService.generate_motivational_content(student.program, risk_factors)
            
            intervention = Intervention(
                student_id=student.id,
                level=1,
                type='automatic',
                content=content,
                status='delivered'  # Se entrega automáticamente
            )
            db.session.add(intervention)
            
            print(f"📧 Intervención automática enviada a {student.name}")
            
        except Exception as e:
            print(f"Error en intervención nivel 1: {e}")
    
    @staticmethod
    def level_2_intervention(student):
        """Intervención Nivel 2: Asignación de mentora"""
        try:
            # Buscar mentora compatible
            mentor = MentorMatchingService.find_best_mentor(student)
            
            intervention_content = "🤝 Intervención de Mentoría Activada\n\n"
            
            if mentor:
                # Crear match con mentora
                existing_match = MentorMatch.query.filter_by(
                    student_id=student.id,
                    status='active'
                ).first()
                
                if not existing_match:
                    match = MentorMatch(
                        student_id=student.id,
                        mentor_id=mentor.id,
                        match_score=MentorMatchingService.calculate_compatibility_score(student, mentor),
                        status='active'
                    )
                    db.session.add(match)
                    
                    # Actualizar contador de mentees
                    mentor.current_mentees = min(mentor.max_mentees, mentor.current_mentees + 1)
                    
                    intervention_content += f"Has sido conectada con tu mentora: {mentor.name}\n"
                    intervention_content += f"Posición actual: {mentor.current_position}\n"
                    intervention_content += f"Programa: {mentor.program}\n\n"
                    intervention_content += "Tu mentora se pondrá en contacto contigo pronto para programar su primera sesión."
                else:
                    intervention_content += f"Continuando mentoría con {mentor.name}"
            else:
                intervention_content += "Estás en lista de espera para asignación de mentora. Te contactaremos pronto."
            
            intervention = Intervention(
                student_id=student.id,
                level=2,
                type='mentor',
                content=intervention_content,
                status='pending'
            )
            db.session.add(intervention)
            
            print(f"👥 Mentoría activada para {student.name}")
            
        except Exception as e:
            print(f"Error en intervención nivel 2: {e}")
    
    @staticmethod
    def level_3_intervention(student):
        """Intervención Nivel 3: Alerta a consejeros académicos"""
        try:
            intervention_content = f"""
            🚨 ALERTA DE ALTO RIESGO - ACCIÓN INMEDIATA REQUERIDA
            
            Estudiante: {student.name}
            Email: {student.email}
            Programa: {student.program}
            Semestre: {student.semester}
            Score de Riesgo: {student.risk_score:.2f}
            
            FACTORES DE RIESGO IDENTIFICADOS:
            • Score de riesgo crítico (≥ 0.8)
            • Múltiples indicadores de deserción
            • Posible síndrome del impostor severo
            • Bajo rendimiento académico y participación
            
            ACCIONES RECOMENDADAS:
            1. Contacto inmediato con la estudiante
            2. Sesión de evaluación psicoeducativa
            3. Plan de recuperación académica personalizado
            4. Seguimiento semanal intensivo
            5. Coordinación con servicios de bienestar estudiantil
            
            Esta alerta fue generada automáticamente por el sistema de retención STEM.
            Tiempo de respuesta recomendado: 24-48 horas.
            """
            
            intervention = Intervention(
                student_id=student.id,
                level=3,
                type='counselor',
                content=intervention_content,
                status='pending'
            )
            db.session.add(intervention)
            
            # Marcar como crítica para notificaciones
            print(f"🚨 ALERTA CRÍTICA: {student.name} requiere intervención inmediata")
            
            # Aquí se enviarían notificaciones a coordinadores académicos
            InterventionSystem.notify_counselors(student, intervention)
            
        except Exception as e:
            print(f"Error en intervención nivel 3: {e}")
    
    @staticmethod
    def notify_counselors(student, intervention):
        """Notificar a consejeros sobre caso crítico"""
        try:
            # En implementación real, esto enviaría emails/SMS a coordinadores
            print(f"📧 Notificación enviada a consejeros académicos")
            print(f"   Estudiante: {student.name} ({student.email})")
            print(f"   Programa: {student.program}")
            print(f"   Riesgo: {student.risk_score:.2f}")
            print(f"   ID Intervención: {intervention.id}")
            
            # Log para auditoria
            print(f"🔍 Log: Intervención crítica #{intervention.id} creada para estudiante #{student.id}")
            
        except Exception as e:
            print(f"Error notificando consejeros: {e}")
    
    @staticmethod
    def update_intervention_effectiveness(intervention_id, rating, feedback=None):
        """Actualizar efectividad de una intervención"""
        try:
            intervention = Intervention.query.get(intervention_id)
            if intervention:
                intervention.effectiveness_rating = rating
                intervention.status = 'completed'
                intervention.completed_at = datetime.utcnow()
                
                if feedback:
                    intervention.content += f"\n\nFeedback: {feedback}"
                
                db.session.commit()
                print(f"✅ Efectividad de intervención #{intervention_id} actualizada: {rating}")
                return True
            
            return False
        except Exception as e:
            print(f"Error actualizando efectividad: {e}")
            return False
    
    @staticmethod
    def get_intervention_analytics():
        """Obtener analíticas de efectividad de intervenciones"""
        try:
            # Estadísticas por nivel
            level_stats = db.session.query(
                Intervention.level,
                db.func.count(Intervention.id).label('total'),
                db.func.avg(Intervention.effectiveness_rating).label('avg_effectiveness'),
                db.func.count(db.case([(Intervention.status == 'completed', 1)])).label('completed')
            ).group_by(Intervention.level).all()
            
            # Estadísticas por tipo
            type_stats = db.session.query(
                Intervention.type,
                db.func.count(Intervention.id).label('total'),
                db.func.avg(Intervention.effectiveness_rating).label('avg_effectiveness')
            ).group_by(Intervention.type).all()
            
            # Tendencias temporales
            from datetime import timedelta
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            recent_interventions = Intervention.query.filter(
                Intervention.created_at >= thirty_days_ago
            ).count()
            
            total_interventions = Intervention.query.count()
            
            return {
                'level_effectiveness': [
                    {
                        'level': stat.level,
                        'total': stat.total,
                        'avg_effectiveness': round(float(stat.avg_effectiveness or 0), 3),
                        'completion_rate': round((stat.completed / stat.total) * 100, 1)
                    } for stat in level_stats
                ],
                'type_effectiveness': [
                    {
                        'type': stat.type,
                        'total': stat.total,
                        'avg_effectiveness': round(float(stat.avg_effectiveness or 0), 3)
                    } for stat in type_stats
                ],
                'recent_activity': {
                    'total_interventions': total_interventions,
                    'recent_30_days': recent_interventions,
                    'activity_rate': round((recent_interventions / max(total_interventions, 1)) * 100, 1)
                }
            }
        except Exception as e:
            print(f"Error obteniendo analíticas de intervención: {e}")
            return {}

class MentorMatchingService:
    """Servicio de matching inteligente entre estudiantes y mentoras"""
    
    @staticmethod
    def find_best_mentor(student):
        """Encontrar la mejor mentora para un estudiante"""
        try:
            # Buscar mentoras disponibles del mismo programa
            available_mentors = Mentor.query.filter(
                Mentor.availability == True,
                Mentor.current_mentees < Mentor.max_mentees,
                Mentor.program == student.program
            ).all()
            
            if not available_mentors:
                # Si no hay del mismo programa, buscar mentoras disponibles de cualquier programa
                available_mentors = Mentor.query.filter(
                    Mentor.availability == True,
                    Mentor.current_mentees < Mentor.max_mentees
                ).all()
            
            if not available_mentors:
                return None
            
            # Calcular score de compatibilidad para cada mentora
            best_mentor = None
            best_score = 0
            
            for mentor in available_mentors:
                score = MentorMatchingService.calculate_compatibility_score(student, mentor)
                if score > best_score:
                    best_score = score
                    best_mentor = mentor
            
            return best_mentor
            
        except Exception as e:
            print(f"Error encontrando mentora: {e}")
            return None
    
    @staticmethod
    def calculate_compatibility_score(student, mentor):
        """Calcular score de compatibilidad entre estudiante y mentora"""
        try:
            score = 0.0
            
            # Programa (40% del score)
            if student.program == mentor.program:
                score += 0.4
            elif mentor.program in ['Ingeniería de Sistemas', 'Ingeniería Industrial', 'Matemáticas']:
                score += 0.2  # Programas relacionados
            
            # Diferencia de experiencia (20%)
            experience_gap = mentor.graduation_year - student.entry_year
            if 3 <= experience_gap <= 7:  # Sweet spot para mentoría
                score += 0.2
            elif 1 <= experience_gap <= 10:
                score += 0.1
            
            # Disponibilidad de la mentora (20%)
            mentor_load = mentor.current_mentees / max(mentor.max_mentees, 1)
            if mentor_load < 0.5:
                score += 0.2
            elif mentor_load < 0.8:
                score += 0.15
            else:
                score += 0.1
            
            # Factor de experiencia y posición (20%)
            if mentor.current_position:
                senior_positions = ['senior', 'lead', 'director', 'manager', 'principal']
                if any(pos in mentor.current_position.lower() for pos in senior_positions):
                    score += 0.2
                else:
                    score += 0.15
            else:
                score += 0.1
            
            return min(1.0, score)
            
        except Exception as e:
            print(f"Error calculando compatibilidad: {e}")
            return 0.0
    
    @staticmethod
    def get_mentor_recommendations(student_id, limit=3):
        """Obtener recomendaciones de mentoras para un estudiante"""
        try:
            student = Student.query.get(student_id)
            if not student:
                return []
            
            # Obtener mentoras disponibles
            available_mentors = Mentor.query.filter(
                Mentor.availability == True,
                Mentor.current_mentees < Mentor.max_mentees
            ).all()
            
            # Calcular scores y ordenar
            mentor_scores = []
            for mentor in available_mentors:
                score = MentorMatchingService.calculate_compatibility_score(student, mentor)
                mentor_scores.append({
                    'mentor': mentor,
                    'compatibility_score': score
                })
            
            # Ordenar por score y tomar los mejores
            mentor_scores.sort(key=lambda x: x['compatibility_score'], reverse=True)
            
            recommendations = []
            for item in mentor_scores[:limit]:
                mentor = item['mentor']
                recommendations.append({
                    'id': mentor.id,
                    'name': mentor.name,
                    'program': mentor.program,
                    'current_position': mentor.current_position,
                    'graduation_year': mentor.graduation_year,
                    'current_mentees': mentor.current_mentees,
                    'max_mentees': mentor.max_mentees,
                    'compatibility_score': round(item['compatibility_score'], 3),
                    'availability_status': 'high' if mentor.current_mentees < mentor.max_mentees * 0.5 else 'medium'
                })
            
            return recommendations
            
        except Exception as e:
            print(f"Error obteniendo recomendaciones de mentoras: {e}")
            return []