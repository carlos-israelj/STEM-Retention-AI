from flask import Blueprint, jsonify, request
from models import Student, Mentor, Intervention, MentorMatch, SupportRequest, db
from datetime import datetime, timedelta

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/mentors')
def get_mentors():
    """Obtener lista de mentoras"""
    try:
        mentors = Mentor.query.all()
        mentors_data = []
        for mentor in mentors:
            mentors_data.append({
                'id': mentor.id,
                'name': mentor.name,
                'email': mentor.email,
                'program': mentor.program,
                'graduation_year': mentor.graduation_year,
                'current_position': mentor.current_position,
                'availability': mentor.availability,
                'current_mentees': mentor.current_mentees,
                'max_mentees': mentor.max_mentees,
                'created_at': mentor.created_at.isoformat()
            })
        return jsonify(mentors_data)
    except Exception as e:
        print(f"Error obteniendo mentoras: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@admin_bp.route('/interventions')
def get_interventions():
    """Obtener todas las intervenciones"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status')
        level = request.args.get('level', type=int)
        
        query = Intervention.query
        
        if status:
            query = query.filter(Intervention.status == status)
        if level:
            query = query.filter(Intervention.level == level)
        
        query = query.order_by(Intervention.created_at.desc())
        
        interventions_paginated = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        interventions_data = []
        for intervention in interventions_paginated.items:
            student = Student.query.get(intervention.student_id)
            interventions_data.append({
                'id': intervention.id,
                'student_id': intervention.student_id,
                'student_name': student.name if student else 'N/A',
                'student_program': student.program if student else 'N/A',
                'level': intervention.level,
                'type': intervention.type,
                'content': intervention.content,
                'status': intervention.status,
                'effectiveness_rating': intervention.effectiveness_rating,
                'created_at': intervention.created_at.isoformat(),
                'completed_at': intervention.completed_at.isoformat() if intervention.completed_at else None
            })
        
        return jsonify({
            'interventions': interventions_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': interventions_paginated.total,
                'pages': interventions_paginated.pages,
                'has_next': interventions_paginated.has_next,
                'has_prev': interventions_paginated.has_prev
            }
        })
    except Exception as e:
        print(f"Error obteniendo intervenciones: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@admin_bp.route('/mentor_matches')
def get_mentor_matches():
    """Obtener asignaciones de mentoras"""
    try:
        matches = db.session.query(
            MentorMatch,
            Student.name.label('student_name'),
            Student.program.label('student_program'),
            Student.risk_score,
            Mentor.name.label('mentor_name'),
            Mentor.current_position
        ).join(Student, MentorMatch.student_id == Student.id)\
         .join(Mentor, MentorMatch.mentor_id == Mentor.id)\
         .filter(MentorMatch.status == 'active').all()
        
        matches_data = []
        for match, student_name, student_program, risk_score, mentor_name, mentor_position in matches:
            matches_data.append({
                'id': match.id,
                'student_id': match.student_id,
                'student_name': student_name,
                'student_program': student_program,
                'student_risk_score': risk_score,
                'mentor_id': match.mentor_id,
                'mentor_name': mentor_name,
                'mentor_position': mentor_position,
                'match_score': match.match_score,
                'status': match.status,
                'created_at': match.created_at.isoformat()
            })
        
        return jsonify(matches_data)
    except Exception as e:
        print(f"Error obteniendo asignaciones de mentoras: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@admin_bp.route('/system_metrics')
def get_system_metrics():
    """Métricas completas del sistema para administradores"""
    try:
        # Métricas de estudiantes
        total_students = Student.query.count()
        high_risk_students = Student.query.filter(Student.risk_score >= 0.7).count()
        medium_risk_students = Student.query.filter(
            Student.risk_score >= 0.4,
            Student.risk_score < 0.7
        ).count()
        low_risk_students = Student.query.filter(Student.risk_score < 0.4).count()
        
        # Métricas de intervenciones
        total_interventions = Intervention.query.count()
        pending_interventions = Intervention.query.filter_by(status='pending').count()
        completed_interventions = Intervention.query.filter_by(status='completed').count()
        effective_interventions = Intervention.query.filter(
            Intervention.effectiveness_rating >= 0.7
        ).count()
        
        # Métricas de mentorías
        total_mentors = Mentor.query.count()
        active_mentors = Mentor.query.filter_by(availability=True).count()
        total_matches = MentorMatch.query.filter_by(status='active').count()
        
        # Métricas de sistema de apoyo
        total_support_requests = SupportRequest.query.count()
        pending_support = SupportRequest.query.filter_by(status='pending').count()
        crisis_requests = SupportRequest.query.filter(
            SupportRequest.priority_score >= 80
        ).count()
        
        # Métricas temporales (últimos 30 días)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_interventions = Intervention.query.filter(
            Intervention.created_at >= thirty_days_ago
        ).count()
        recent_support_requests = SupportRequest.query.filter(
            SupportRequest.created_at >= thirty_days_ago
        ).count()
        
        # Distribución por programa
        program_distribution = db.session.query(
            Student.program,
            db.func.count(Student.id).label('total'),
            db.func.avg(Student.risk_score).label('avg_risk')
        ).group_by(Student.program).all()
        
        # Efectividad de intervenciones por nivel
        intervention_effectiveness = db.session.query(
            Intervention.level,
            db.func.count(Intervention.id).label('total'),
            db.func.avg(Intervention.effectiveness_rating).label('avg_effectiveness')
        ).filter(Intervention.effectiveness_rating.isnot(None))\
         .group_by(Intervention.level).all()
        
        return jsonify({
            'students': {
                'total': total_students,
                'high_risk': high_risk_students,
                'medium_risk': medium_risk_students,
                'low_risk': low_risk_students,
                'risk_percentage': {
                    'high': round((high_risk_students / max(total_students, 1)) * 100, 1),
                    'medium': round((medium_risk_students / max(total_students, 1)) * 100, 1),
                    'low': round((low_risk_students / max(total_students, 1)) * 100, 1)
                }
            },
            'interventions': {
                'total': total_interventions,
                'pending': pending_interventions,
                'completed': completed_interventions,
                'effective': effective_interventions,
                'completion_rate': round((completed_interventions / max(total_interventions, 1)) * 100, 1),
                'effectiveness_rate': round((effective_interventions / max(total_interventions, 1)) * 100, 1),
                'recent_30_days': recent_interventions
            },
            'mentoring': {
                'total_mentors': total_mentors,
                'active_mentors': active_mentors,
                'total_matches': total_matches,
                'utilization_rate': round((total_matches / max(active_mentors * 3, 1)) * 100, 1)  # Asumiendo 3 mentees max
            },
            'support_system': {
                'total_requests': total_support_requests,
                'pending': pending_support,
                'crisis_level': crisis_requests,
                'recent_30_days': recent_support_requests,
                'response_rate': round(((total_support_requests - pending_support) / max(total_support_requests, 1)) * 100, 1)
            },
            'program_distribution': [
                {
                    'program': item.program,
                    'total_students': item.total,
                    'average_risk': round(float(item.avg_risk), 3)
                } for item in program_distribution
            ],
            'intervention_effectiveness': [
                {
                    'level': item.level,
                    'total_interventions': item.total,
                    'average_effectiveness': round(float(item.avg_effectiveness or 0), 3)
                } for item in intervention_effectiveness
            ]
        })
    except Exception as e:
        print(f"Error obteniendo métricas del sistema: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@admin_bp.route('/performance_analytics')
def get_performance_analytics():
    """Analíticas de rendimiento del sistema"""
    try:
        # Tendencias de riesgo por mes
        risk_trends = []
        for i in range(6):  # Últimos 6 meses
            month_start = datetime.utcnow().replace(day=1) - timedelta(days=30*i)
            month_end = month_start + timedelta(days=30)
            
            month_avg_risk = db.session.query(
                db.func.avg(Student.risk_score)
            ).filter(
                Student.last_risk_update >= month_start,
                Student.last_risk_update < month_end
            ).scalar()
            
            risk_trends.append({
                'month': month_start.strftime('%Y-%m'),
                'average_risk': round(float(month_avg_risk or 0), 3)
            })
        
        # Efectividad de intervenciones por tipo
        intervention_types = db.session.query(
            Intervention.type,
            db.func.count(Intervention.id).label('total'),
            db.func.avg(Intervention.effectiveness_rating).label('avg_effectiveness')
        ).filter(Intervention.effectiveness_rating.isnot(None))\
         .group_by(Intervention.type).all()
        
        # Categorías más frecuentes en sistema de apoyo
        support_categories = db.session.query(
            SupportRequest.category,
            db.func.count(SupportRequest.id).label('total'),
            db.func.avg(SupportRequest.priority_score).label('avg_priority')
        ).group_by(SupportRequest.category).all()
        
        # Tiempo promedio de resolución de solicitudes de apoyo
        resolved_requests = SupportRequest.query.filter(
            SupportRequest.resolved_at.isnot(None)
        ).all()
        
        total_resolution_time = 0
        resolution_count = 0
        for request in resolved_requests:
            if request.resolved_at and request.created_at:
                resolution_time = (request.resolved_at - request.created_at).total_seconds() / 3600  # horas
                total_resolution_time += resolution_time
                resolution_count += 1
        
        avg_resolution_time = total_resolution_time / max(resolution_count, 1)
        
        return jsonify({
            'risk_trends': risk_trends,
            'intervention_effectiveness_by_type': [
                {
                    'type': item.type,
                    'total': item.total,
                    'average_effectiveness': round(float(item.avg_effectiveness), 3)
                } for item in intervention_types
            ],
            'support_categories_analysis': [
                {
                    'category': item.category,
                    'total_requests': item.total,
                    'average_priority': round(float(item.avg_priority), 1)
                } for item in support_categories
            ],
            'resolution_metrics': {
                'average_resolution_time_hours': round(avg_resolution_time, 1),
                'total_resolved_requests': resolution_count,
                'resolution_rate': round((resolution_count / max(SupportRequest.query.count(), 1)) * 100, 1)
            }
        })
    except Exception as e:
        print(f"Error obteniendo analíticas de rendimiento: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@admin_bp.route('/generate_report')
def generate_system_report():
    """Generar reporte completo del sistema"""
    try:
        report_date = datetime.utcnow()
        
        # Estadísticas generales
        total_students = Student.query.count()
        high_risk_count = Student.query.filter(Student.risk_score >= 0.7).count()
        interventions_last_month = Intervention.query.filter(
            Intervention.created_at >= report_date - timedelta(days=30)
        ).count()
        
        # ROI estimado
        from config import Config
        roi_config = Config.ROI_CONFIG
        
        estimated_students_retained = high_risk_count * roi_config['projected_retention_improvement']
        total_revenue_retained = estimated_students_retained * roi_config['revenue_per_retained_student']
        total_intervention_cost = interventions_last_month * roi_config['cost_per_intervention']
        estimated_roi = total_revenue_retained - total_intervention_cost
        
        # Alertas del sistema
        alerts = []
        
        if high_risk_count > total_students * 0.3:  # Más del 30% en alto riesgo
            alerts.append({
                'type': 'warning',
                'message': f'Alto porcentaje de estudiantes en riesgo: {round((high_risk_count/total_students)*100, 1)}%'
            })
        
        pending_interventions = Intervention.query.filter_by(status='pending').count()
        if pending_interventions > 10:
            alerts.append({
                'type': 'warning',
                'message': f'{pending_interventions} intervenciones pendientes requieren atención'
            })
        
        crisis_requests = SupportRequest.query.filter(
            SupportRequest.priority_score >= 80,
            SupportRequest.status == 'pending'
        ).count()
        if crisis_requests > 0:
            alerts.append({
                'type': 'critical',
                'message': f'{crisis_requests} solicitudes de crisis pendientes'
            })
        
        # Recomendaciones
        recommendations = []
        
        if high_risk_count > 5:
            recommendations.append("Considerar aumentar recursos de mentorías para estudiantes de alto riesgo")
        
        if interventions_last_month < high_risk_count * 0.5:
            recommendations.append("Incrementar frecuencia de intervenciones preventivas")
        
        avg_support_priority = db.session.query(
            db.func.avg(SupportRequest.priority_score)
        ).scalar() or 0
        
        if avg_support_priority > 60:
            recommendations.append("El nivel promedio de urgencia en solicitudes de apoyo es alto - revisar recursos")
        
        return jsonify({
            'report_generated_at': report_date.isoformat(),
            'summary': {
                'total_students': total_students,
                'high_risk_students': high_risk_count,
                'interventions_last_month': interventions_last_month,
                'estimated_roi': round(estimated_roi, 2),
                'retention_improvement': f"{roi_config['projected_retention_improvement']*100}%"
            },
            'financial_impact': {
                'estimated_students_retained': round(estimated_students_retained, 1),
                'total_revenue_retained': round(total_revenue_retained, 2),
                'total_intervention_cost': round(total_intervention_cost, 2),
                'net_roi': round(estimated_roi, 2),
                'roi_ratio': round(estimated_roi / max(total_intervention_cost, 1), 2)
            },
            'system_alerts': alerts,
            'recommendations': recommendations,
            'system_health': 'good' if len(alerts) == 0 else 'warning' if any(a['type'] == 'warning' for a in alerts) else 'critical'
        })
    except Exception as e:
        print(f"Error generando reporte del sistema: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@admin_bp.route('/simulate_all_data')
def simulate_all_data():
    """Simular datos completos del sistema"""
    try:
        from services.data_simulator import DataSimulator
        
        simulator = DataSimulator()
        result = simulator.simulate_complete_system()
        
        return jsonify(result)
    except Exception as e:
        print(f"Error simulando datos: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500