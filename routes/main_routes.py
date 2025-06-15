from flask import Blueprint, render_template, jsonify, redirect
from models import Student, Intervention, SupportRequest, db
from datetime import datetime, timedelta

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    """Pantalla de inicio del sistema"""
    return render_template('home.html')

@main_bp.route('/dashboard')
def dashboard():
    """Dashboard administrativo"""
    return render_template('dashboard.html')

@main_bp.route('/student/<int:student_id>')
def student_detail(student_id):
    """Vista detallada de un estudiante"""
    return render_template('student_detail.html', student_id=student_id)

@main_bp.route('/student_support.html')
def serve_student_support():
    """Servir la página de apoyo estudiantil"""
    return render_template('student_support.html')

@main_bp.route('/student/support')
def student_support():
    """Página de apoyo para estudiantes"""
    return render_template('student_support.html')

@main_bp.route('/admin/support')
def support_admin_dashboard():
    """Dashboard administrativo para el sistema de apoyo"""
    return render_template('support_admin.html')

# Rutas adicionales de compatibilidad
@main_bp.route('/index')
def index_redirect():
    """Redirección desde /index a la página de inicio"""
    return redirect('/')

@main_bp.route('/inicio')
def inicio():
    """Ruta alternativa en español para la página de inicio"""
    return render_template('home.html')

@main_bp.route('/api/dashboard_stats')
def get_dashboard_stats():
    """Estadísticas principales del dashboard"""
    try:
        total_students = Student.query.count()
        high_risk = Student.query.filter(Student.risk_score > 0.6).count()
        active_interventions = Intervention.query.filter_by(status='pending').count()
        
        return jsonify({
            'total_students': total_students,
            'high_risk_percentage': round((high_risk/total_students)*100, 1) if total_students > 0 else 0,
            'active_interventions': active_interventions,
            'retention_improvement': "25%"  # Proyección
        })
    except Exception as e:
        print(f"Error obteniendo estadísticas del dashboard: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@main_bp.route('/api/impact_metrics')
def get_impact_metrics():
    """Métricas de impacto financiero"""
    try:
        from config import Config
        
        total_students = Student.query.count()
        students_at_risk = Student.query.filter(Student.risk_score > 0.6).count()
        interventions_successful = Intervention.query.filter(
            Intervention.effectiveness_rating > 0.7
        ).count()
        total_interventions = Intervention.query.count()
        
        # Obtener configuración de ROI
        roi_config = Config.ROI_CONFIG
        cost_per_intervention = roi_config['cost_per_intervention']
        revenue_per_retained_student = roi_config['revenue_per_retained_student']
        retention_improvement = roi_config['projected_retention_improvement']
        
        intervention_success_rate = (interventions_successful / max(total_interventions, 1)) * 100
        
        return jsonify({
            'students_identified_at_risk': students_at_risk,
            'intervention_success_rate': f'{intervention_success_rate:.0f}%',
            'estimated_retention_increase': f'{retention_improvement*100:.0f}%',
            'roi_per_student': revenue_per_retained_student - cost_per_intervention,
            'projected_annual_savings': int(students_at_risk * revenue_per_retained_student * retention_improvement),
            'cost_effectiveness': f'${cost_per_intervention}/estudiante',
            'total_students_monitored': total_students
        })
    except Exception as e:
        print(f"Error obteniendo métricas de impacto: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@main_bp.route('/api/mentors')
def get_mentors():
    """Obtener lista de mentoras (ruta de compatibilidad)"""
    try:
        from models import Mentor
        mentors = Mentor.query.all()
        mentors_data = []
        for mentor in mentors:
            mentors_data.append({
                'id': mentor.id,
                'name': mentor.name,
                'program': mentor.program,
                'availability': mentor.availability,
                'current_mentees': mentor.current_mentees,
                'max_mentees': mentor.max_mentees
            })
        return jsonify(mentors_data)
    except Exception as e:
        print(f"Error obteniendo mentoras: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@main_bp.route('/api/simulate_data')
def simulate_data_compat():
    """Ruta de compatibilidad para simular datos"""
    try:
        from services.data_simulator import DataSimulator
        simulator = DataSimulator()
        result = simulator.simulate_complete_system()
        return jsonify(result)
    except Exception as e:
        print(f"Error simulando datos: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@main_bp.route('/api/system_overview')
def get_system_overview():
    """Vista general del sistema completo"""
    try:
        # Estadísticas de estudiantes
        total_students = Student.query.count()
        high_risk_students = Student.query.filter(Student.risk_score >= 0.7).count()
        medium_risk_students = Student.query.filter(
            Student.risk_score >= 0.4,
            Student.risk_score < 0.7
        ).count()
        low_risk_students = Student.query.filter(Student.risk_score < 0.4).count()
        
        # Estadísticas de intervenciones
        total_interventions = Intervention.query.count()
        pending_interventions = Intervention.query.filter_by(status='pending').count()
        completed_interventions = Intervention.query.filter_by(status='completed').count()
        
        # Estadísticas de sistema de apoyo
        total_support_requests = SupportRequest.query.count()
        pending_support = SupportRequest.query.filter_by(status='pending').count()
        high_priority_support = SupportRequest.query.filter(
            SupportRequest.priority_score >= 80
        ).count()
        
        # Métricas de últimos 7 días
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_interventions = Intervention.query.filter(
            Intervention.created_at >= week_ago
        ).count()
        recent_support = SupportRequest.query.filter(
            SupportRequest.created_at >= week_ago
        ).count()
        
        return jsonify({
            'system_status': 'operational',
            'students': {
                'total': total_students,
                'high_risk': high_risk_students,
                'medium_risk': medium_risk_students,
                'low_risk': low_risk_students,
                'risk_distribution': {
                    'high': round((high_risk_students / max(total_students, 1)) * 100, 1),
                    'medium': round((medium_risk_students / max(total_students, 1)) * 100, 1),
                    'low': round((low_risk_students / max(total_students, 1)) * 100, 1)
                }
            },
            'interventions': {
                'total': total_interventions,
                'pending': pending_interventions,
                'completed': completed_interventions,
                'recent_7_days': recent_interventions,
                'completion_rate': round((completed_interventions / max(total_interventions, 1)) * 100, 1)
            },
            'support_system': {
                'total_requests': total_support_requests,
                'pending': pending_support,
                'high_priority': high_priority_support,
                'recent_7_days': recent_support,
                'response_rate': round(((total_support_requests - pending_support) / max(total_support_requests, 1)) * 100, 1)
            },
            'alerts': {
                'critical_students': high_risk_students,
                'pending_interventions': pending_interventions,
                'crisis_requests': high_priority_support,
                'requires_attention': pending_interventions + high_priority_support > 10
            }
        })
    except Exception as e:
        print(f"Error obteniendo vista general del sistema: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500