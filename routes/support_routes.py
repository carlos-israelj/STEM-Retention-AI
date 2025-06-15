from flask import Blueprint, request, jsonify
from models import SupportRequest, SupportResponse, db
from services.support_services import SupportPrioritizer, SupportNotificationSystem
from datetime import datetime, timedelta

support_bp = Blueprint('support', __name__)

@support_bp.route('/requests', methods=['POST'])
def create_support_request():
    """Crear nueva solicitud de apoyo"""
    try:
        data = request.get_json()
        
        # Validación básica
        if not data.get('message'):
            return jsonify({'error': 'El mensaje es requerido'}), 400
        
        if not data.get('category'):
            return jsonify({'error': 'La categoría es requerida'}), 400
        
        # Calcular score de prioridad
        priority_score = SupportPrioritizer.calculate_priority_score(data)
        
        # Crear solicitud
        support_request = SupportRequest(
            anonymous=data.get('anonymous', False),
            student_name=data.get('student_name') if not data.get('anonymous') else None,
            student_email=data.get('student_email'),
            urgency=data.get('urgency', 'medium'),
            category=data.get('category'),
            message=data.get('message'),
            previous_help=data.get('previous_help'),
            contact_preference=data.get('contact_preference', 'email'),
            priority_score=priority_score
        )
        
        db.session.add(support_request)
        db.session.commit()
        
        # Notificar al equipo de apoyo
        SupportNotificationSystem.notify_support_team(support_request)
        
        # Si es una crisis, crear intervención automática
        if priority_score >= 80:
            SupportPrioritizer.create_crisis_intervention(support_request)
        
        return jsonify({
            'success': True,
            'request_id': support_request.id,
            'priority_score': priority_score,
            'message': 'Solicitud enviada exitosamente. Nuestro equipo se pondrá en contacto contigo pronto.'
        })
        
    except Exception as e:
        print(f"Error creando solicitud de apoyo: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@support_bp.route('/requests', methods=['GET'])
def get_support_requests():
    """Obtener todas las solicitudes de apoyo (para staff)"""
    try:
        # Filtros opcionales
        status = request.args.get('status')
        urgency = request.args.get('urgency')
        category = request.args.get('category')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        query = SupportRequest.query
        
        if status:
            query = query.filter(SupportRequest.status == status)
        if urgency:
            query = query.filter(SupportRequest.urgency == urgency)
        if category:
            query = query.filter(SupportRequest.category == category)
        
        # Ordenar por prioridad y fecha
        query = query.order_by(
            SupportRequest.priority_score.desc(),
            SupportRequest.created_at.desc()
        )
        
        requests_paginated = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        requests_data = []
        for req in requests_paginated.items:
            requests_data.append({
                'id': req.id,
                'anonymous': req.anonymous,
                'student_name': req.student_name,
                'student_email': req.student_email,
                'urgency': req.urgency,
                'category': req.category,
                'message': req.message,
                'status': req.status,
                'priority_score': req.priority_score,
                'assigned_to': req.assigned_to,
                'created_at': req.created_at.isoformat(),
                'updated_at': req.updated_at.isoformat()
            })
        
        return jsonify({
            'requests': requests_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': requests_paginated.total,
                'pages': requests_paginated.pages,
                'has_next': requests_paginated.has_next,
                'has_prev': requests_paginated.has_prev
            }
        })
        
    except Exception as e:
        print(f"Error obteniendo solicitudes: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@support_bp.route('/requests/<int:request_id>', methods=['GET'])
def get_support_request_detail(request_id):
    """Obtener detalle de una solicitud específica"""
    try:
        support_request = SupportRequest.query.get_or_404(request_id)
        
        # Obtener respuestas asociadas
        responses = SupportResponse.query.filter_by(
            request_id=request_id
        ).order_by(SupportResponse.created_at.asc()).all()
        
        responses_data = []
        for response in responses:
            responses_data.append({
                'id': response.id,
                'responder_name': response.responder_name,
                'responder_role': response.responder_role,
                'response_text': response.response_text,
                'response_type': response.response_type,
                'is_public': response.is_public,
                'created_at': response.created_at.isoformat()
            })
        
        request_data = {
            'id': support_request.id,
            'anonymous': support_request.anonymous,
            'student_name': support_request.student_name,
            'student_email': support_request.student_email,
            'urgency': support_request.urgency,
            'category': support_request.category,
            'message': support_request.message,
            'previous_help': support_request.previous_help,
            'contact_preference': support_request.contact_preference,
            'status': support_request.status,
            'priority_score': support_request.priority_score,
            'assigned_to': support_request.assigned_to,
            'response': support_request.response,
            'created_at': support_request.created_at.isoformat(),
            'updated_at': support_request.updated_at.isoformat(),
            'resolved_at': support_request.resolved_at.isoformat() if support_request.resolved_at else None,
            'responses': responses_data
        }
        
        return jsonify(request_data)
        
    except Exception as e:
        print(f"Error obteniendo detalle de solicitud: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@support_bp.route('/requests/<int:request_id>/respond', methods=['POST'])
def respond_to_support_request(request_id):
    """Responder a una solicitud de apoyo"""
    try:
        data = request.get_json()
        support_request = SupportRequest.query.get_or_404(request_id)
        
        # Crear respuesta
        response = SupportResponse(
            request_id=request_id,
            responder_name=data.get('responder_name', 'Sistema de Apoyo'),
            responder_role=data.get('responder_role', 'support_staff'),
            response_text=data.get('response_text'),
            response_type=data.get('response_type', 'follow_up'),
            is_public=data.get('is_public', True)
        )
        
        db.session.add(response)
        
        # Actualizar solicitud
        support_request.status = data.get('new_status', support_request.status)
        support_request.assigned_to = data.get('assigned_to', support_request.assigned_to)
        support_request.updated_at = datetime.utcnow()
        
        if data.get('new_status') == 'resolved':
            support_request.resolved_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Respuesta enviada exitosamente'})
        
    except Exception as e:
        print(f"Error respondiendo solicitud: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@support_bp.route('/requests/search')
def search_support_requests():
    """Búsqueda avanzada de solicitudes de apoyo"""
    try:
        # Parámetros de búsqueda
        search_term = request.args.get('q', '')
        status = request.args.get('status')
        category = request.args.get('category')
        urgency = request.args.get('urgency')
        priority_min = request.args.get('priority_min', type=float)
        priority_max = request.args.get('priority_max', type=float)
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        anonymous_only = request.args.get('anonymous_only', type=bool)
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        query = SupportRequest.query
        
        # Búsqueda por texto
        if search_term:
            search_filter = db.or_(
                SupportRequest.message.contains(search_term),
                SupportRequest.student_name.contains(search_term),
                SupportRequest.student_email.contains(search_term)
            )
            query = query.filter(search_filter)
        
        # Filtros
        if status:
            query = query.filter(SupportRequest.status == status)
        if category:
            query = query.filter(SupportRequest.category == category)
        if urgency:
            query = query.filter(SupportRequest.urgency == urgency)
        if priority_min is not None:
            query = query.filter(SupportRequest.priority_score >= priority_min)
        if priority_max is not None:
            query = query.filter(SupportRequest.priority_score <= priority_max)
        if anonymous_only:
            query = query.filter(SupportRequest.anonymous == True)
        
        # Filtros de fecha
        if date_from:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(SupportRequest.created_at >= date_from_obj)
        if date_to:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(SupportRequest.created_at < date_to_obj)
        
        # Ordenamiento
        sort_by = request.args.get('sort_by', 'priority')
        if sort_by == 'priority':
            query = query.order_by(SupportRequest.priority_score.desc())
        elif sort_by == 'date':
            query = query.order_by(SupportRequest.created_at.desc())
        elif sort_by == 'status':
            query = query.order_by(SupportRequest.status)
        
        # Paginación
        results = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        requests_data = []
        for req in results.items:
            requests_data.append({
                'id': req.id,
                'anonymous': req.anonymous,
                'student_name': req.student_name,
                'urgency': req.urgency,
                'category': req.category,
                'status': req.status,
                'priority_score': req.priority_score,
                'created_at': req.created_at.isoformat(),
                'message_preview': req.message[:150] + '...' if len(req.message) > 150 else req.message
            })
        
        return jsonify({
            'requests': requests_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': results.total,
                'pages': results.pages,
                'has_next': results.has_next,
                'has_prev': results.has_prev
            },
            'search_params': {
                'search_term': search_term,
                'total_found': results.total
            }
        })
        
    except Exception as e:
        print(f"Error en búsqueda de solicitudes: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@support_bp.route('/stats')
def get_support_stats():
    """Estadísticas del sistema de apoyo"""
    try:
        # Estadísticas generales
        total_requests = SupportRequest.query.count()
        pending_requests = SupportRequest.query.filter_by(status='pending').count()
        high_priority = SupportRequest.query.filter(SupportRequest.priority_score >= 80).count()
        resolved_requests = SupportRequest.query.filter_by(status='resolved').count()
        
        # Métricas de tiempo de respuesta
        recent_requests = SupportRequest.query.filter(
            SupportRequest.created_at >= datetime.utcnow() - timedelta(days=7)
        ).count()
        
        # Distribución por categoría
        category_stats = db.session.query(
            SupportRequest.category,
            db.func.count(SupportRequest.id)
        ).group_by(SupportRequest.category).all()
        
        # Distribución por urgencia
        urgency_stats = db.session.query(
            SupportRequest.urgency,
            db.func.count(SupportRequest.id)
        ).group_by(SupportRequest.urgency).all()
        
        # Tasa de resolución
        resolution_rate = (resolved_requests / max(total_requests, 1)) * 100
        
        return jsonify({
            'total_requests': total_requests,
            'pending_requests': pending_requests,
            'high_priority_requests': high_priority,
            'recent_requests_7_days': recent_requests,
            'category_distribution': dict(category_stats),
            'urgency_distribution': dict(urgency_stats),
            'response_rate': round((total_requests - pending_requests) / max(total_requests, 1) * 100, 1),
            'resolution_rate': round(resolution_rate, 1)
        })
        
    except Exception as e:
        print(f"Error obteniendo estadísticas: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@support_bp.route('/dashboard_metrics')
def get_support_dashboard_metrics():
    """Métricas para el dashboard de administración"""
    try:
        # Métricas básicas
        total_requests = SupportRequest.query.count()
        pending_requests = SupportRequest.query.filter_by(status='pending').count()
        high_priority = SupportRequest.query.filter(SupportRequest.priority_score >= 80).count()
        resolved_requests = SupportRequest.query.filter_by(status='resolved').count()
        
        # Métricas de tiempo de respuesta
        recent_requests = SupportRequest.query.filter(
            SupportRequest.created_at >= datetime.utcnow() - timedelta(days=7)
        ).count()
        
        # Distribución por categoría (últimos 30 días)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        category_distribution = db.session.query(
            SupportRequest.category,
            db.func.count(SupportRequest.id)
        ).filter(
            SupportRequest.created_at >= thirty_days_ago
        ).group_by(SupportRequest.category).all()
        
        # Tendencia semanal
        weekly_trend = []
        for i in range(4):  # Últimas 4 semanas
            week_start = datetime.utcnow() - timedelta(weeks=i+1)
            week_end = datetime.utcnow() - timedelta(weeks=i)
            
            week_count = SupportRequest.query.filter(
                SupportRequest.created_at >= week_start,
                SupportRequest.created_at < week_end
            ).count()
            
            weekly_trend.append({
                'week': f'Semana {4-i}',
                'requests': week_count
            })
        
        # Tasa de resolución
        resolution_rate = (resolved_requests / max(total_requests, 1)) * 100
        
        return jsonify({
            'total_requests': total_requests,
            'pending_requests': pending_requests,
            'high_priority_requests': high_priority,
            'resolved_requests': resolved_requests,
            'recent_requests_7_days': recent_requests,
            'resolution_rate': round(resolution_rate, 1),
            'category_distribution': dict(category_distribution),
            'weekly_trend': weekly_trend,
            'average_priority_score': round(
                db.session.query(db.func.avg(SupportRequest.priority_score)).scalar() or 0, 1
            )
        })
        
    except Exception as e:
        print(f"Error obteniendo métricas del dashboard: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@support_bp.route('/predictive_analysis')
def support_predictive_analysis():
    """Análisis predictivo del sistema de apoyo"""
    try:
        # Análisis de tendencias
        current_month = datetime.utcnow().month
        current_year = datetime.utcnow().year
        
        # Solicitudes del mes actual
        month_start = datetime(current_year, current_month, 1)
        current_month_requests = SupportRequest.query.filter(
            SupportRequest.created_at >= month_start
        ).count()
        
        # Solicitudes del mes anterior
        if current_month == 1:
            prev_month, prev_year = 12, current_year - 1
        else:
            prev_month, prev_year = current_month - 1, current_year
            
        prev_month_start = datetime(prev_year, prev_month, 1)
        if current_month == 12:
            prev_month_end = datetime(current_year + 1, 1, 1)
        else:
            prev_month_end = datetime(current_year, current_month, 1)
            
        prev_month_requests = SupportRequest.query.filter(
            SupportRequest.created_at >= prev_month_start,
            SupportRequest.created_at < prev_month_end
        ).count()
        
        # Calcular tendencia
        if prev_month_requests > 0:
            trend_percentage = ((current_month_requests - prev_month_requests) / prev_month_requests) * 100
        else:
            trend_percentage = 100 if current_month_requests > 0 else 0
        
        # Predicción de carga de trabajo
        avg_daily_requests = current_month_requests / datetime.utcnow().day
        predicted_month_total = int(avg_daily_requests * 30)  # Proyección mensual
        
        # Análisis por categorías de riesgo
        category_trends = {}
        for category in ['emotional', 'academic', 'social', 'career', 'financial']:
            category_count = SupportRequest.query.filter(
                SupportRequest.category == category,
                SupportRequest.created_at >= month_start
            ).count()
            category_trends[category] = category_count
        
        # Identificar categoría en crecimiento
        trending_category = max(category_trends.items(), key=lambda x: x[1]) if category_trends else ('emotional', 0)
        
        return jsonify({
            'current_month_requests': current_month_requests,
            'previous_month_requests': prev_month_requests,
            'trend_percentage': round(trend_percentage, 1),
            'trend_direction': 'up' if trend_percentage > 0 else 'down' if trend_percentage < 0 else 'stable',
            'predicted_month_total': predicted_month_total,
            'average_daily_requests': round(avg_daily_requests, 1),
            'category_trends': category_trends,
            'trending_category': trending_category[0],
            'workload_alert': predicted_month_total > 50,  # Alert si se predicen más de 50 solicitudes
            'recommendations': [
                f"La categoría '{trending_category[0]}' está mostrando mayor actividad",
                "Considerar aumentar recursos de apoyo" if predicted_month_total > 50 else "Carga de trabajo manejable",
                "Tendencia ascendente en solicitudes" if trend_percentage > 20 else "Solicitudes estables"
            ]
        })
        
    except Exception as e:
        print(f"Error en análisis predictivo: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@support_bp.route('/create_sample_data')
def create_support_sample_data():
    """Endpoint para crear datos de prueba del sistema de apoyo"""
    try:
        from services.data_simulator import create_sample_support_data
        create_sample_support_data()
        
        stats = {
            'total_requests': SupportRequest.query.count(),
            'pending_requests': SupportRequest.query.filter_by(status='pending').count(),
            'responses': SupportResponse.query.count()
        }
        
        return jsonify({
            'success': True,
            'message': 'Datos de ejemplo creados exitosamente',
            'stats': stats
        })
    except Exception as e:
        print(f"Error creando datos de ejemplo: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500