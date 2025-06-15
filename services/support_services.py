from models import Student, Intervention, SupportRequest, db
from config import Config
from datetime import datetime

class SupportPrioritizer:
    """Sistema de priorización de solicitudes de apoyo"""
    
    @staticmethod
    def calculate_priority_score(request_data):
        """
        Calcula un score de prioridad basado en múltiples factores
        Score de 0-100, donde 100 es máxima prioridad
        """
        score = 0.0
        
        # Factor de urgencia (40% del score)
        urgency_weights = {
            'high': 40.0,
            'medium': 25.0,
            'low': 10.0
        }
        score += urgency_weights.get(request_data.get('urgency', 'low'), 10.0)
        
        # Factor de categoría (30% del score)
        category_weights = {
            'emotional': 30.0,  # Prioridad máxima para salud mental
            'academic': 20.0,
            'social': 15.0,
            'career': 10.0,
            'financial': 25.0,  # Importante para retención
            'other': 12.0
        }
        score += category_weights.get(request_data.get('category', 'other'), 12.0)
        
        # Análisis de contenido (30% del score)
        message = request_data.get('message', '').lower()
        
        # Obtener palabras clave de crisis de la configuración
        crisis_keywords = Config.SUPPORT_CONFIG['EMERGENCY_KEYWORDS']
        
        # Palabras clave de riesgo académico
        academic_risk_keywords = [
            'reprobar', 'fallar', 'abandonar', 'desertar', 'renunciar',
            'no entiendo nada', 'perdida', 'atrasada', 'suspender'
        ]
        
        # Palabras clave de aislamiento social
        isolation_keywords = [
            'sola', 'aislada', 'no tengo amigos', 'no encajo',
            'discriminación', 'exclusión', 'bullying', 'acoso'
        ]
        
        # Aplicar puntajes por keywords
        if any(keyword in message for keyword in crisis_keywords):
            score += 25.0  # Máxima prioridad para crisis
        elif any(keyword in message for keyword in academic_risk_keywords):
            score += 15.0
        elif any(keyword in message for keyword in isolation_keywords):
            score += 12.0
        
        # Bonus por longitud del mensaje (indica más detalle/urgencia)
        message_length = len(message)
        if message_length > 500:
            score += 5.0
        elif message_length > 200:
            score += 2.0
        
        return min(100.0, score)
    
    @staticmethod
    def create_crisis_intervention(support_request):
        """Crear intervención automática para casos de crisis"""
        try:
            # Buscar si hay un estudiante registrado con el email
            student = None
            if support_request.student_email:
                student = Student.query.filter_by(
                    email=support_request.student_email
                ).first()
            
            intervention_content = f"""
            ALERTA DE CRISIS DETECTADA - Solicitud de Apoyo #{support_request.id}
            
            Estudiante: {'ANÓNIMO' if support_request.anonymous else support_request.student_name or 'No identificado'}
            Categoría: {support_request.category}
            Urgencia: {support_request.urgency}
            Score de Prioridad: {support_request.priority_score}
            
            Mensaje de la estudiante:
            {support_request.message[:500]}...
            
            ACCIONES REQUERIDAS:
            1. Contacto inmediato con servicios de salud mental
            2. Verificación de seguridad de la estudiante
            3. Plan de seguimiento intensivo
            4. Notificación a coordinación académica
            
            Preferencia de contacto: {support_request.contact_preference}
            """
            
            if student:
                # Crear intervención vinculada al perfil del estudiante
                intervention = Intervention(
                    student_id=student.id,
                    level=3,  # Máximo nivel
                    type='counselor',
                    content=intervention_content,
                    status='pending'
                )
                db.session.add(intervention)
                
                # Actualizar nivel de intervención del estudiante
                student.intervention_level = 3
                
            db.session.commit()
            print(f"✅ Intervención de crisis creada para solicitud #{support_request.id}")
            
        except Exception as e:
            print(f"Error creando intervención de crisis: {e}")

class SupportNotificationSystem:
    """Sistema de notificaciones para el equipo de apoyo"""
    
    @staticmethod
    def notify_support_team(request):
        """Notificar al equipo de apoyo sobre nueva solicitud"""
        priority_score = request.priority_score
        
        if priority_score >= Config.SUPPORT_CONFIG['CRISIS_THRESHOLD']:
            # Crisis - notificación inmediata
            SupportNotificationSystem.send_emergency_alert(request)
        elif priority_score >= Config.SUPPORT_CONFIG['HIGH_PRIORITY_THRESHOLD']:
            # Alta prioridad - notificación en 1 hora
            SupportNotificationSystem.schedule_alert(request, delay_hours=1)
        else:
            # Prioridad normal - notificación diaria
            SupportNotificationSystem.schedule_alert(request, delay_hours=24)
    
    @staticmethod
    def send_emergency_alert(request):
        """Alerta inmediata para crisis"""
        print(f"🚨 ALERTA DE CRISIS - ID: {request.id}")
        print(f"Estudiante: {'ANÓNIMO' if request.anonymous else request.student_name}")
        print(f"Urgencia: {request.urgency.upper()}")
        print(f"Categoría: {request.category}")
        print(f"Score de prioridad: {request.priority_score}")
        print(f"Mensaje: {request.message[:100]}...")
        
        # Aquí iría la lógica real de notificación (email, SMS, Slack, etc.)
        # Por ejemplo:
        # - Enviar email a equipo de crisis
        # - Notificación push a coordinadores
        # - Webhook a sistema de gestión
        
    @staticmethod
    def schedule_alert(request, delay_hours):
        """Programar alerta diferida"""
        print(f"📅 Alerta programada para {delay_hours}h - ID: {request.id}")
        # Aquí iría la lógica de programación de alertas
        # Por ejemplo:
        # - Agregar a cola de tareas con delay
        # - Programar notificación diferida
        # - Actualizar dashboard de pendientes

class PerplexityService:
    """Servicio para generar contenido motivacional con IA"""
    
    @staticmethod
    def generate_motivational_content(student_program, risk_factors):
        """Generar contenido motivacional personalizado"""
        try:
            import requests
            
            headers = {
                "Authorization": f"Bearer {Config.PERPLEXITY_API_KEY}",
                "Content-Type": "application/json"
            }
            
            prompt = f"""
            Genera contenido motivacional específico para una estudiante mujer de {student_program} 
            que está mostrando señales de riesgo de deserción. Factores de riesgo identificados: {risk_factors}.
            El contenido debe ser empoderador, específico para STEM y culturalmente sensible.
            Incluye historias de éxito de mujeres en el campo y estrategias prácticas.
            """
            
            data = {
                "model": "llama-3.1-sonar-small-128k-online",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 500
            }
            
            response = requests.post(Config.PERPLEXITY_URL, headers=headers, json=data)
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
            else:
                return PerplexityService.get_default_content(student_program)
        except Exception as e:
            print(f"Error generando contenido con Perplexity: {e}")
            return PerplexityService.get_default_content(student_program)
    
    @staticmethod
    def get_default_content(student_program):
        """Contenido motivacional predeterminado por programa"""
        default_content = {
            'Ingeniería de Sistemas': """
            🌟 Recuerda que en tecnología, la diversidad de perspectivas es nuestra mayor fortaleza.
            
            Mujeres pioneras como Ada Lovelace y Grace Hopper sentaron las bases de lo que hoy llamamos programación. 
            Tu perspectiva única es exactamente lo que la industria tech necesita.
            
            💡 Estrategias que pueden ayudarte:
            • Únete a comunidades como Women in Tech o PyLadies
            • Busca mentoras en la industria
            • Practica coding un poco cada día
            • Celebra cada pequeño logro
            
            ¡Tu futuro en tech es brillante! 💻✨
            """,
            'Ingeniería Industrial': """
            🏭 La ingeniería industrial necesita más mujeres líderes como tú.
            
            Desde Lillian Gilbreth, pionera en gestión científica, hasta ejecutivas modernas como Mary Barra (GM), 
            las mujeres han transformado la industria con enfoques innovadores y sostenibles.
            
            💪 Fortalezas que puedes desarrollar:
            • Pensamiento sistémico y holístico
            • Habilidades de comunicación y liderazgo
            • Enfoque en sostenibilidad e impacto social
            • Análisis detallado y mejora continua
            
            El mundo necesita tu visión para crear sistemas más eficientes y humanos. 🌍
            """,
            'Matemáticas': """
            🔢 Las matemáticas son el lenguaje universal, y tu voz es esencial.
            
            Mujeres como Emmy Noether, Katherine Johnson y Maryam Mirzakhani han demostrado que 
            las matemáticas florecen con perspectivas diversas y mentes brillantes como la tuya.
            
            🧮 Tu camino matemático puede incluir:
            • Investigación pura y aplicada
            • Análisis de datos y machine learning
            • Finanzas cuantitativas
            • Criptografía y seguridad
            
            Cada problema que resuelves abre nuevas posibilidades para el mundo. ∞
            """
        }
        
        return default_content.get(student_program, 
            "Recuerda que eres capaz de lograr grandes cosas en STEM. Tu perspectiva única es valiosa y necesaria. ¡Sigue adelante! 🌟")

class SupportAnalytics:
    """Servicio de análisis y métricas del sistema de apoyo"""
    
    @staticmethod
    def get_effectiveness_metrics():
        """Calcular métricas de efectividad del sistema"""
        try:
            total_requests = SupportRequest.query.count()
            resolved_requests = SupportRequest.query.filter_by(status='resolved').count()
            crisis_requests = SupportRequest.query.filter(
                SupportRequest.priority_score >= Config.SUPPORT_CONFIG['CRISIS_THRESHOLD']
            ).count()
            
            # Tiempo promedio de respuesta
            from sqlalchemy import func
            avg_response_time = db.session.query(
                func.avg(
                    func.julianday(SupportRequest.updated_at) - 
                    func.julianday(SupportRequest.created_at)
                ) * 24  # Convertir a horas
            ).filter(SupportRequest.updated_at.isnot(None)).scalar() or 0
            
            # Distribución de categorías
            category_distribution = db.session.query(
                SupportRequest.category,
                func.count(SupportRequest.id),
                func.avg(SupportRequest.priority_score)
            ).group_by(SupportRequest.category).all()
            
            return {
                'total_requests': total_requests,
                'resolution_rate': (resolved_requests / max(total_requests, 1)) * 100,
                'crisis_rate': (crisis_requests / max(total_requests, 1)) * 100,
                'avg_response_time_hours': round(avg_response_time, 2),
                'category_insights': [
                    {
                        'category': cat,
                        'count': count,
                        'avg_priority': round(float(avg_priority), 1)
                    } for cat, count, avg_priority in category_distribution
                ]
            }
        except Exception as e:
            print(f"Error calculando métricas de efectividad: {e}")
            return {}
    
    @staticmethod
    def identify_trends():
        """Identificar tendencias en el sistema de apoyo"""
        try:
            from datetime import timedelta
            
            # Comparar últimos 30 días vs 30 días anteriores
            now = datetime.utcnow()
            thirty_days_ago = now - timedelta(days=30)
            sixty_days_ago = now - timedelta(days=60)
            
            recent_requests = SupportRequest.query.filter(
                SupportRequest.created_at >= thirty_days_ago
            ).count()
            
            previous_requests = SupportRequest.query.filter(
                SupportRequest.created_at >= sixty_days_ago,
                SupportRequest.created_at < thirty_days_ago
            ).count()
            
            # Calcular tendencia
            if previous_requests > 0:
                trend_percentage = ((recent_requests - previous_requests) / previous_requests) * 100
            else:
                trend_percentage = 100 if recent_requests > 0 else 0
            
            # Categorías en crecimiento
            recent_categories = db.session.query(
                SupportRequest.category,
                db.func.count(SupportRequest.id)
            ).filter(
                SupportRequest.created_at >= thirty_days_ago
            ).group_by(SupportRequest.category).all()
            
            previous_categories = db.session.query(
                SupportRequest.category,
                db.func.count(SupportRequest.id)
            ).filter(
                SupportRequest.created_at >= sixty_days_ago,
                SupportRequest.created_at < thirty_days_ago
            ).group_by(SupportRequest.category).all()
            
            # Analizar cambios por categoría
            category_trends = {}
            recent_dict = dict(recent_categories)
            previous_dict = dict(previous_categories)
            
            for category in recent_dict:
                recent_count = recent_dict[category]
                previous_count = previous_dict.get(category, 0)
                
                if previous_count > 0:
                    category_change = ((recent_count - previous_count) / previous_count) * 100
                else:
                    category_change = 100 if recent_count > 0 else 0
                
                category_trends[category] = {
                    'recent_count': recent_count,
                    'previous_count': previous_count,
                    'change_percentage': round(category_change, 1)
                }
            
            return {
                'overall_trend': {
                    'recent_requests': recent_requests,
                    'previous_requests': previous_requests,
                    'change_percentage': round(trend_percentage, 1),
                    'direction': 'increasing' if trend_percentage > 5 else 'decreasing' if trend_percentage < -5 else 'stable'
                },
                'category_trends': category_trends,
                'recommendations': SupportAnalytics.generate_recommendations(trend_percentage, category_trends)
            }
        except Exception as e:
            print(f"Error identificando tendencias: {e}")
            return {}
    
    @staticmethod
    def generate_recommendations(overall_trend, category_trends):
        """Generar recomendaciones basadas en tendencias"""
        recommendations = []
        
        if overall_trend > 20:
            recommendations.append("Considerar aumentar recursos del equipo de apoyo debido al incremento significativo en solicitudes")
        
        # Identificar categoría con mayor crecimiento
        if category_trends:
            fastest_growing = max(
                category_trends.items(),
                key=lambda x: x[1]['change_percentage']
            )
            
            if fastest_growing[1]['change_percentage'] > 50:
                category_name = fastest_growing[0]
                recommendations.append(f"La categoría '{category_name}' muestra crecimiento acelerado - revisar recursos específicos")
        
        # Verificar crisis
        crisis_count = SupportRequest.query.filter(
            SupportRequest.priority_score >= Config.SUPPORT_CONFIG['CRISIS_THRESHOLD'],
            SupportRequest.created_at >= datetime.utcnow() - timedelta(days=7)
        ).count()
        
        if crisis_count > 3:
            recommendations.append("Alto número de solicitudes de crisis en la última semana - activar protocolos de emergencia")
        
        if not recommendations:
            recommendations.append("Sistema operando dentro de parámetros normales")
        
        return recommendations