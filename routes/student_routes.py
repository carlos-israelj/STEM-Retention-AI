from flask import Blueprint, jsonify, request
from models import Student, AcademicRecord, BehavioralRecord, Intervention, MentorMatch, Mentor, SupportRequest, db
from datetime import datetime

student_bp = Blueprint('students', __name__)

@student_bp.route('/')
def get_students():
    """Obtener lista de todos los estudiantes"""
    try:
        students = Student.query.all()
        students_data = []
        for student in students:
            students_data.append({
                'id': student.id,
                'name': student.name,
                'email': student.email,
                'program': student.program,
                'semester': student.semester,
                'risk_score': student.risk_score,
                'intervention_level': student.intervention_level,
                'last_risk_update': student.last_risk_update.isoformat() if student.last_risk_update else None
            })
        return jsonify(students_data)
    except Exception as e:
        print(f"Error obteniendo estudiantes: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@student_bp.route('/<int:student_id>')
def get_student_detail(student_id):
    """Obtener información detallada de un estudiante"""
    try:
        student = Student.query.get_or_404(student_id)
        
        # Obtener registros académicos
        academic_records = AcademicRecord.query.filter_by(
            student_id=student_id
        ).order_by(AcademicRecord.date_recorded.desc()).all()
        
        # Obtener registros comportamentales
        behavioral_records = BehavioralRecord.query.filter_by(
            student_id=student_id
        ).order_by(BehavioralRecord.date_recorded.desc()).all()
        
        # Obtener intervenciones
        interventions = Intervention.query.filter_by(
            student_id=student_id
        ).order_by(Intervention.created_at.desc()).all()
        
        # Obtener mentora asignada
        mentor_match = MentorMatch.query.filter_by(
            student_id=student_id, status='active'
        ).first()
        mentor = None
        if mentor_match:
            mentor = Mentor.query.get(mentor_match.mentor_id)
        
        student_data = {
            'id': student.id,
            'name': student.name,
            'email': student.email,
            'program': student.program,
            'semester': student.semester,
            'entry_year': student.entry_year,
            'risk_score': student.risk_score,
            'intervention_level': student.intervention_level,
            'last_risk_update': student.last_risk_update.isoformat() if student.last_risk_update else None,
            'created_at': student.created_at.isoformat(),
            'academic_records': [{
                'id': record.id,
                'subject': record.subject,
                'grade': record.grade,
                'attendance_rate': record.attendance_rate,
                'participation_score': record.participation_score,
                'assignment_completion': record.assignment_completion,
                'date_recorded': record.date_recorded.isoformat()
            } for record in academic_records],
            'behavioral_records': [{
                'id': record.id,
                'oral_participation': record.oral_participation,
                'self_assessment_confidence': record.self_assessment_confidence,
                'teacher_interaction_frequency': record.teacher_interaction_frequency,
                'group_work_engagement': record.group_work_engagement,
                'impostor_syndrome_indicators': record.impostor_syndrome_indicators,
                'date_recorded': record.date_recorded.isoformat()
            } for record in behavioral_records],
            'interventions': [{
                'id': intervention.id,
                'level': intervention.level,
                'type': intervention.type,
                'content': intervention.content,
                'status': intervention.status,
                'effectiveness_rating': intervention.effectiveness_rating,
                'created_at': intervention.created_at.isoformat(),
                'completed_at': intervention.completed_at.isoformat() if intervention.completed_at else None
            } for intervention in interventions],
            'mentor': {
                'id': mentor.id,
                'name': mentor.name,
                'email': mentor.email,
                'program': mentor.program,
                'current_position': mentor.current_position,
                'match_score': mentor_match.match_score
            } if mentor else None
        }
        
        return jsonify(student_data)
    except Exception as e:
        print(f"Error obteniendo detalle del estudiante: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@student_bp.route('/<int:student_id>/risk')
def update_risk_score(student_id):
    """Actualizar score de riesgo de un estudiante"""
    try:
        # Importar aquí para evitar dependencias circulares
        from services.risk_predictor import RiskPredictor
        from services.intervention_system import InterventionSystem
        
        risk_predictor = RiskPredictor()
        risk_score = risk_predictor.predict_risk(student_id)
        
        student = Student.query.get(student_id)
        if student:
            student.risk_score = risk_score
            student.last_risk_update = datetime.utcnow()
            
            # Trigger intervention if needed
            InterventionSystem.trigger_intervention(student_id, risk_score)
            
            db.session.commit()
            return jsonify({
                'risk_score': risk_score,
                'status': 'updated',
                'last_update': student.last_risk_update.isoformat()
            })
        else:
            return jsonify({'error': 'Estudiante no encontrado'}), 404
    except Exception as e:
        print(f"Error actualizando score de riesgo: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@student_bp.route('/<int:student_id>/support_history')
def get_student_support_history(student_id):
    """Obtener historial de solicitudes de apoyo de un estudiante"""
    try:
        student = Student.query.get_or_404(student_id)
        
        # Buscar solicitudes por email
        support_requests = SupportRequest.query.filter_by(
            student_email=student.email
        ).order_by(SupportRequest.created_at.desc()).all()
        
        requests_data = []
        for req in support_requests:
            requests_data.append({
                'id': req.id,
                'urgency': req.urgency,
                'category': req.category,
                'status': req.status,
                'priority_score': req.priority_score,
                'created_at': req.created_at.isoformat(),
                'resolved_at': req.resolved_at.isoformat() if req.resolved_at else None,
                'message_preview': req.message[:100] + '...' if len(req.message) > 100 else req.message
            })
        
        return jsonify({
            'student_id': student_id,
            'student_name': student.name,
            'student_email': student.email,
            'support_requests': requests_data,
            'total_requests': len(requests_data),
            'has_critical_requests': any(req.priority_score >= 80 for req in support_requests)
        })
    except Exception as e:
        print(f"Error obteniendo historial de apoyo: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@student_bp.route('/<int:student_id>/interventions')
def get_student_interventions(student_id):
    """Obtener intervenciones de un estudiante específico"""
    try:
        interventions = Intervention.query.filter_by(
            student_id=student_id
        ).order_by(Intervention.created_at.desc()).all()
        
        interventions_data = []
        for intervention in interventions:
            interventions_data.append({
                'id': intervention.id,
                'level': intervention.level,
                'type': intervention.type,
                'content': intervention.content,
                'status': intervention.status,
                'effectiveness_rating': intervention.effectiveness_rating,
                'created_at': intervention.created_at.isoformat(),
                'completed_at': intervention.completed_at.isoformat() if intervention.completed_at else None
            })
        
        return jsonify({
            'student_id': student_id,
            'interventions': interventions_data,
            'total_interventions': len(interventions_data)
        })
    except Exception as e:
        print(f"Error obteniendo intervenciones: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@student_bp.route('/search')
def search_students():
    """Búsqueda avanzada de estudiantes"""
    try:
        # Parámetros de búsqueda
        search_term = request.args.get('q', '')
        program = request.args.get('program')
        semester = request.args.get('semester', type=int)
        risk_min = request.args.get('risk_min', type=float)
        risk_max = request.args.get('risk_max', type=float)
        intervention_level = request.args.get('intervention_level', type=int)
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        query = Student.query
        
        # Búsqueda por texto
        if search_term:
            search_filter = db.or_(
                Student.name.contains(search_term),
                Student.email.contains(search_term),
                Student.program.contains(search_term)
            )
            query = query.filter(search_filter)
        
        # Filtros
        if program:
            query = query.filter(Student.program == program)
        if semester:
            query = query.filter(Student.semester == semester)
        if risk_min is not None:
            query = query.filter(Student.risk_score >= risk_min)
        if risk_max is not None:
            query = query.filter(Student.risk_score <= risk_max)
        if intervention_level is not None:
            query = query.filter(Student.intervention_level == intervention_level)
        
        # Ordenamiento
        sort_by = request.args.get('sort_by', 'risk_desc')
        if sort_by == 'risk_desc':
            query = query.order_by(Student.risk_score.desc())
        elif sort_by == 'risk_asc':
            query = query.order_by(Student.risk_score.asc())
        elif sort_by == 'name':
            query = query.order_by(Student.name)
        elif sort_by == 'program':
            query = query.order_by(Student.program, Student.name)
        elif sort_by == 'semester':
            query = query.order_by(Student.semester.desc(), Student.name)
        
        # Paginación
        results = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        students_data = []
        for student in results.items:
            students_data.append({
                'id': student.id,
                'name': student.name,
                'email': student.email,
                'program': student.program,
                'semester': student.semester,
                'risk_score': student.risk_score,
                'intervention_level': student.intervention_level,
                'last_risk_update': student.last_risk_update.isoformat() if student.last_risk_update else None
            })
        
        return jsonify({
            'students': students_data,
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
        print(f"Error en búsqueda de estudiantes: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@student_bp.route('/analytics')
def get_student_analytics():
    """Analíticas de estudiantes"""
    try:
        # Distribución por programa
        program_stats = db.session.query(
            Student.program,
            db.func.count(Student.id).label('total'),
            db.func.avg(Student.risk_score).label('avg_risk')
        ).group_by(Student.program).all()
        
        # Distribución por semestre
        semester_stats = db.session.query(
            Student.semester,
            db.func.count(Student.id).label('total'),
            db.func.avg(Student.risk_score).label('avg_risk')
        ).group_by(Student.semester).order_by(Student.semester).all()
        
        # Distribución de riesgo
        risk_distribution = {
            'low': Student.query.filter(Student.risk_score < 0.4).count(),
            'medium': Student.query.filter(
                Student.risk_score >= 0.4,
                Student.risk_score < 0.7
            ).count(),
            'high': Student.query.filter(Student.risk_score >= 0.7).count()
        }
        
        # Tendencias de riesgo por año de ingreso
        entry_year_stats = db.session.query(
            Student.entry_year,
            db.func.count(Student.id).label('total'),
            db.func.avg(Student.risk_score).label('avg_risk')
        ).group_by(Student.entry_year).order_by(Student.entry_year).all()
        
        return jsonify({
            'program_distribution': [
                {
                    'program': stat.program,
                    'total_students': stat.total,
                    'average_risk': round(float(stat.avg_risk), 3)
                } for stat in program_stats
            ],
            'semester_distribution': [
                {
                    'semester': stat.semester,
                    'total_students': stat.total,
                    'average_risk': round(float(stat.avg_risk), 3)
                } for stat in semester_stats
            ],
            'risk_distribution': risk_distribution,
            'entry_year_trends': [
                {
                    'entry_year': stat.entry_year,
                    'total_students': stat.total,
                    'average_risk': round(float(stat.avg_risk), 3)
                } for stat in entry_year_stats
            ]
        })
    except Exception as e:
        print(f"Error obteniendo analíticas de estudiantes: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500