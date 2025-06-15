from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# ===== MODELOS PRINCIPALES =====

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    program = db.Column(db.String(100), nullable=False)
    semester = db.Column(db.Integer, nullable=False)
    entry_year = db.Column(db.Integer, nullable=False)
    risk_score = db.Column(db.Float, default=0.0)
    last_risk_update = db.Column(db.DateTime, default=datetime.utcnow)
    intervention_level = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    academic_records = db.relationship('AcademicRecord', backref='student', lazy=True)
    behavioral_records = db.relationship('BehavioralRecord', backref='student', lazy=True)
    interventions = db.relationship('Intervention', backref='student', lazy=True)

class Mentor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    program = db.Column(db.String(100), nullable=False)
    graduation_year = db.Column(db.Integer, nullable=False)
    current_position = db.Column(db.String(200))
    availability = db.Column(db.Boolean, default=True)
    max_mentees = db.Column(db.Integer, default=3)
    current_mentees = db.Column(db.Integer, default=0)
    personality_traits = db.Column(db.Text)  # JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ===== MODELOS DE REGISTROS ACADÉMICOS =====

class AcademicRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    grade = db.Column(db.Float)
    attendance_rate = db.Column(db.Float)
    participation_score = db.Column(db.Float)
    assignment_completion = db.Column(db.Float)
    date_recorded = db.Column(db.DateTime, default=datetime.utcnow)

class BehavioralRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    oral_participation = db.Column(db.Float)
    self_assessment_confidence = db.Column(db.Float)
    teacher_interaction_frequency = db.Column(db.Float)
    group_work_engagement = db.Column(db.Float)
    impostor_syndrome_indicators = db.Column(db.Float)
    date_recorded = db.Column(db.DateTime, default=datetime.utcnow)

# ===== MODELOS DE INTERVENCIONES =====

class Intervention(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    level = db.Column(db.Integer, nullable=False)  # 1, 2, or 3
    type = db.Column(db.String(50), nullable=False)  # 'automatic', 'mentor', 'counselor'
    content = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # pending, delivered, completed
    effectiveness_rating = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)

class MentorMatch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    mentor_id = db.Column(db.Integer, db.ForeignKey('mentor.id'), nullable=False)
    match_score = db.Column(db.Float)
    status = db.Column(db.String(20), default='active')  # active, completed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ===== MODELOS DEL SISTEMA DE APOYO =====

class SupportRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    anonymous = db.Column(db.Boolean, default=False)
    student_name = db.Column(db.String(100))  # Null si es anónimo
    student_email = db.Column(db.String(100))
    urgency = db.Column(db.String(20), nullable=False)  # low, medium, high
    category = db.Column(db.String(50), nullable=False)  # academic, emotional, social, career, financial, other
    message = db.Column(db.Text, nullable=False)
    previous_help = db.Column(db.Text)
    contact_preference = db.Column(db.String(50))  # email, phone, in-person, video-call, no-contact
    status = db.Column(db.String(20), default='pending')  # pending, in-progress, resolved, closed
    assigned_to = db.Column(db.String(100))  # Staff member assigned
    response = db.Column(db.Text)  # Response from support team
    priority_score = db.Column(db.Float, default=0.0)  # Auto-calculated priority
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)

class SupportResponse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('support_request.id'), nullable=False)
    responder_name = db.Column(db.String(100), nullable=False)
    responder_role = db.Column(db.String(50))  # counselor, mentor, peer_support, coordinator
    response_text = db.Column(db.Text, nullable=False)
    response_type = db.Column(db.String(30))  # initial_contact, follow_up, resolution, referral
    is_public = db.Column(db.Boolean, default=True)  # Whether student can see this response
    created_at = db.Column(db.DateTime, default=datetime.utcnow)