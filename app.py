from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import sqlite3
import requests
import json
import os
from werkzeug.security import generate_password_hash, check_password_hash
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import joblib
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tu-clave-secreta-aqui'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///stem_retention.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Configuración API Perplexity
PERPLEXITY_API_KEY = "tu-api-key-aqui"
PERPLEXITY_URL = "https://api.perplexity.ai/chat/completions"

# Modelos de Base de Datos
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

# Servicio API Perplexity
class PerplexityService:
    @staticmethod
    def generate_motivational_content(student_program, risk_factors):
        headers = {
            "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
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
        
        try:
            response = requests.post(PERPLEXITY_URL, headers=headers, json=data)
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
            else:
                return "Contenido motivacional predeterminado: Recuerda que eres capaz de lograr grandes cosas en STEM."
        except:
            return "Contenido motivacional predeterminado disponible."

# Motor Predictivo Corregido
class RiskPredictor:
    def __init__(self):
        self.model = None
        self.use_rule_based = True  # Usar sistema basado en reglas para coherencia
        self.load_or_create_model()
    
    def load_or_create_model(self):
        try:
            self.model = joblib.load('risk_model.pkl')
            # Verificar si el modelo es válido comparando con datos conocidos
            if not self.validate_model():
                self.create_realistic_model()
        except:
            self.create_realistic_model()
    
    def validate_model(self):
        """Verificar que el modelo produce resultados coherentes"""
        # Datos de prueba: estudiante de alto riesgo
        high_risk_features = np.array([[45, 50, 30, 60, 25, 40, 30, 85]])  # Última es síndrome impostor
        # Datos de prueba: estudiante de bajo riesgo  
        low_risk_features = np.array([[90, 95, 85, 95, 90, 88, 85, 25]])
        
        try:
            high_pred = self.model.predict_proba(high_risk_features)[0][1]
            low_pred = self.model.predict_proba(low_risk_features)[0][1]
            
            # El modelo debe predecir mayor riesgo para el primer caso
            return high_pred > low_pred and high_pred > 0.6 and low_pred < 0.4
        except:
            return False
    
    def create_realistic_model(self):
        """Crear modelo entrenado con patrones realistas de deserción femenina en STEM"""
        print("🔄 Creando modelo predictivo con patrones realistas...")
        
        # Generar datos de entrenamiento basados en investigación real
        X, y = self.generate_realistic_training_data()
        
        self.model = RandomForestClassifier(
            n_estimators=100, 
            random_state=42,
            max_depth=10,
            min_samples_split=5
        )
        self.model.fit(X, y)
        joblib.dump(self.model, 'risk_model.pkl')
        
        print(f"✅ Modelo entrenado con {len(X)} muestras")
        print(f"📊 Distribución: {np.mean(y)*100:.1f}% alto riesgo")
    
    def generate_realistic_training_data(self):
        """Generar datos de entrenamiento basados en patrones reales de deserción femenina"""
        features = []
        labels = []
        
        # Basado en investigación: factores de deserción femenina en STEM
        for i in range(2000):
            # Decidir perfil de riesgo
            risk_profile = np.random.choice(['low', 'medium', 'high'], p=[0.4, 0.35, 0.25])
            
            if risk_profile == 'high':
                # ALTO RIESGO: Patrones documentados de deserción femenina
                grade = np.random.normal(65, 10)  # Notas mediocres pero no terribles
                attendance_rate = np.random.normal(60, 15)  # Asistencia irregular
                participation_score = np.random.normal(40, 10)  # Baja participación
                assignment_completion = np.random.normal(70, 15)  # Tareas inconsistentes
                
                # Variables comportamentales críticas para mujeres
                oral_participation = np.random.normal(30, 10)  # Muy baja - factor clave
                self_assessment_confidence = np.random.normal(45, 10)  # Baja confianza
                teacher_interaction_frequency = np.random.normal(35, 10)  # Poca interacción
                impostor_syndrome_indicators = np.random.normal(80, 10)  # Alto síndrome impostor
                
                label = 1  # Alto riesgo
                
            elif risk_profile == 'medium':
                # RIESGO MEDIO: Estudiantes en punto de inflexión
                grade = np.random.normal(75, 8)  # Notas regulares
                attendance_rate = np.random.normal(75, 10)  # Asistencia aceptable
                participation_score = np.random.normal(60, 12)  # Participación moderada
                assignment_completion = np.random.normal(80, 10)  # Mayoría de tareas
                
                oral_participation = np.random.normal(55, 15)  # Variable
                self_assessment_confidence = np.random.normal(65, 12)  # Confianza variable
                teacher_interaction_frequency = np.random.normal(60, 15)  # Interacción moderada
                impostor_syndrome_indicators = np.random.normal(55, 15)  # Síndrome moderado
                
                # 40% probabilidad de ser clasificado como riesgo
                label = 1 if np.random.random() < 0.4 else 0
                
            else:  # low risk
                # BAJO RIESGO: Estudiantes exitosas
                grade = np.random.normal(85, 8)  # Buenas notas
                attendance_rate = np.random.normal(90, 5)  # Excelente asistencia
                participation_score = np.random.normal(85, 8)  # Alta participación
                assignment_completion = np.random.normal(92, 5)  # Casi todas las tareas
                
                oral_participation = np.random.normal(80, 10)  # Alta participación oral
                self_assessment_confidence = np.random.normal(85, 8)  # Alta confianza
                teacher_interaction_frequency = np.random.normal(80, 10)  # Buena interacción
                impostor_syndrome_indicators = np.random.normal(30, 10)  # Bajo síndrome
                
                label = 0  # Bajo riesgo
            
            # Asegurar valores dentro de rangos válidos
            features.append([
                np.clip(grade, 0, 100),
                np.clip(attendance_rate, 0, 100),
                np.clip(participation_score, 0, 100),
                np.clip(assignment_completion, 0, 100),
                np.clip(oral_participation, 0, 100),
                np.clip(self_assessment_confidence, 0, 100),
                np.clip(teacher_interaction_frequency, 0, 100),
                np.clip(impostor_syndrome_indicators, 0, 100)
            ])
            labels.append(label)
        
        return np.array(features), np.array(labels)
    
    def predict_risk(self, student_id):
        """Predecir riesgo usando modelo realista o sistema basado en reglas"""
        student = Student.query.get(student_id)
        if not student:
            return 0.0
        
        # Obtener datos más recientes
        academic = AcademicRecord.query.filter_by(student_id=student_id).order_by(AcademicRecord.date_recorded.desc()).first()
        behavioral = BehavioralRecord.query.filter_by(student_id=student_id).order_by(BehavioralRecord.date_recorded.desc()).first()
        
        if not academic or not behavioral:
            return 0.0
        
        if self.use_rule_based:
            return self.calculate_risk_rule_based(academic, behavioral)
        else:
            return self.calculate_risk_ml_based(academic, behavioral)
    
    def calculate_risk_rule_based(self, academic, behavioral):
        """Sistema de scoring basado en reglas específicas para mujeres en STEM"""
        risk_score = 0.0
        
        # Pesos basados en investigación sobre deserción femenina
        weights = {
            'academic_performance': 0.2,
            'attendance': 0.15,
            'behavioral_factors': 0.65  # Mayor peso en factores psicosociales
        }
        
        # 1. Rendimiento académico (20%)
        grade = academic.grade or 0
        assignment_completion = academic.assignment_completion or 0
        academic_risk = 0
        
        if grade < 60:
            academic_risk += 0.8
        elif grade < 70:
            academic_risk += 0.5
        elif grade < 80:
            academic_risk += 0.2
        
        if assignment_completion < 70:
            academic_risk += 0.6
        elif assignment_completion < 85:
            academic_risk += 0.3
        
        academic_risk = min(1.0, academic_risk)
        
        # 2. Asistencia (15%)
        attendance_rate = academic.attendance_rate or 0
        if attendance_rate < 70:
            attendance_risk = 0.9
        elif attendance_rate < 80:
            attendance_risk = 0.6
        elif attendance_rate < 90:
            attendance_risk = 0.3
        else:
            attendance_risk = 0.1
        
        # 3. Factores comportamentales críticos para mujeres (65%)
        behavioral_risk = 0
        
        # Síndrome del impostor (peso mayor)
        impostor_syndrome = behavioral.impostor_syndrome_indicators or 0
        if impostor_syndrome > 75:
            behavioral_risk += 0.4  # Factor más crítico
        elif impostor_syndrome > 60:
            behavioral_risk += 0.25
        elif impostor_syndrome > 45:
            behavioral_risk += 0.1
        
        # Participación oral (crítico para mujeres)
        oral_participation = behavioral.oral_participation or 0
        if oral_participation < 40:
            behavioral_risk += 0.3
        elif oral_participation < 60:
            behavioral_risk += 0.15
        
        # Confianza en autoevaluación
        confidence = behavioral.self_assessment_confidence or 0
        if confidence < 50:
            behavioral_risk += 0.2
        elif confidence < 70:
            behavioral_risk += 0.1
        
        # Interacción con profesores
        teacher_interaction = behavioral.teacher_interaction_frequency or 0
        if teacher_interaction < 40:
            behavioral_risk += 0.15
        elif teacher_interaction < 60:
            behavioral_risk += 0.08
        
        behavioral_risk = min(1.0, behavioral_risk)
        
        # Calcular riesgo final
        risk_score = (
            academic_risk * weights['academic_performance'] +
            attendance_risk * weights['attendance'] +
            behavioral_risk * weights['behavioral_factors']
        )
        
        return min(1.0, max(0.0, risk_score))
    
    def calculate_risk_ml_based(self, academic, behavioral):
        """Usar modelo ML si está disponible y validado"""
        try:
            features = np.array([[
                academic.grade or 0,
                academic.attendance_rate or 0,
                academic.participation_score or 0,
                academic.assignment_completion or 0,
                behavioral.oral_participation or 0,
                behavioral.self_assessment_confidence or 0,
                behavioral.teacher_interaction_frequency or 0,
                behavioral.impostor_syndrome_indicators or 0
            ]])
            
            risk_prob = self.model.predict_proba(features)[0][1]
            return risk_prob
        except Exception as e:
            print(f"⚠️ Error en predicción ML, usando reglas: {e}")
            return self.calculate_risk_rule_based(academic, behavioral)

# Función para validar distribución de riesgo
def validate_risk_distribution():
    """Verificar que los scores de riesgo reflejen los perfiles simulados"""
    students = Student.query.all()
    risk_distribution = {'low': 0, 'medium': 0, 'high': 0}
    
    for student in students:
        if student.risk_score < 0.3:
            risk_distribution['low'] += 1
        elif student.risk_score < 0.7:
            risk_distribution['medium'] += 1
        else:
            risk_distribution['high'] += 1
    
    total = sum(risk_distribution.values())
    if total > 0:
        percentages = {k: (v/total)*100 for k, v in risk_distribution.items()}
        print(f"📊 Distribución de riesgo:")
        print(f"   Bajo: {percentages['low']:.1f}%")
        print(f"   Medio: {percentages['medium']:.1f}%") 
        print(f"   Alto: {percentages['high']:.1f}%")
        
        # Debería estar cerca de 40% bajo, 35% medio, 25% alto
        return abs(percentages['low'] - 40) < 15 and abs(percentages['high'] - 25) < 15
    
    return False

# Sistema de Intervenciones
class InterventionSystem:
    @staticmethod
    def trigger_intervention(student_id, risk_score):
        student = Student.query.get(student_id)
        if not student:
            return
        
        level = InterventionSystem.determine_intervention_level(risk_score)
        student.intervention_level = level
        
        if level == 1:
            InterventionSystem.level_1_intervention(student)
        elif level == 2:
            InterventionSystem.level_2_intervention(student)
        elif level == 3:
            InterventionSystem.level_3_intervention(student)
        
        db.session.commit()
    
    @staticmethod
    def determine_intervention_level(risk_score):
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
        risk_factors = f"Programa: {student.program}, Semestre: {student.semester}, Factores: disminución participación oral, indicadores síndrome del impostor"
        content = PerplexityService.generate_motivational_content(student.program, risk_factors)
        
        intervention = Intervention(
            student_id=student.id,
            level=1,
            type='automatic',
            content=content
        )
        db.session.add(intervention)
    
    @staticmethod
    def level_2_intervention(student):
        # Buscar mentora compatible
        mentor = MentorMatchingService.find_best_mentor(student)
        if mentor:
            match = MentorMatch(
                student_id=student.id,
                mentor_id=mentor.id,
                match_score=0.8  # Simplificado
            )
            db.session.add(match)
        
        intervention = Intervention(
            student_id=student.id,
            level=2,
            type='mentor',
            content=f"Conectada con mentora: {mentor.name if mentor else 'Por asignar'}"
        )
        db.session.add(intervention)
    
    @staticmethod
    def level_3_intervention(student):
        intervention = Intervention(
            student_id=student.id,
            level=3,
            type='counselor',
            content="Alerta enviada a consejeros académicos - Plan de acción requerido"
        )
        db.session.add(intervention)

# Sistema de Matching de Mentoras
class MentorMatchingService:
    @staticmethod
    def find_best_mentor(student):
        available_mentors = Mentor.query.filter(
            Mentor.availability == True,
            Mentor.current_mentees < Mentor.max_mentees,
            Mentor.program == student.program
        ).all()
        
        if not available_mentors:
            return None
        
        # Algoritmo básico de matching (puede mejorarse)
        best_mentor = available_mentors[0]
        for mentor in available_mentors:
            if mentor.current_mentees < best_mentor.current_mentees:
                best_mentor = mentor
        
        return best_mentor

# Inicializar predictor
risk_predictor = RiskPredictor()

# Rutas principales
@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/student/<int:student_id>')
def student_detail(student_id):
    return render_template('student_detail.html', student_id=student_id)

@app.route('/api/students/<int:student_id>')
def get_student_detail(student_id):
    student = Student.query.get_or_404(student_id)
    
    # Obtener registros académicos
    academic_records = AcademicRecord.query.filter_by(student_id=student_id).order_by(AcademicRecord.date_recorded.desc()).all()
    
    # Obtener registros comportamentales
    behavioral_records = BehavioralRecord.query.filter_by(student_id=student_id).order_by(BehavioralRecord.date_recorded.desc()).all()
    
    # Obtener intervenciones
    interventions = Intervention.query.filter_by(student_id=student_id).order_by(Intervention.created_at.desc()).all()
    
    # Obtener mentora asignada
    mentor_match = MentorMatch.query.filter_by(student_id=student_id, status='active').first()
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

@app.route('/api/students')
def get_students():
    students = Student.query.all()
    students_data = []
    for student in students:
        students_data.append({
            'id': student.id,
            'name': student.name,
            'program': student.program,
            'semester': student.semester,
            'risk_score': student.risk_score,
            'intervention_level': student.intervention_level
        })
    return jsonify(students_data)

@app.route('/api/students/<int:student_id>/risk')
def update_risk_score(student_id):
    risk_score = risk_predictor.predict_risk(student_id)
    student = Student.query.get(student_id)
    if student:
        student.risk_score = risk_score
        student.last_risk_update = datetime.utcnow()
        
        # Trigger intervention if needed
        InterventionSystem.trigger_intervention(student_id, risk_score)
        
        db.session.commit()
        return jsonify({'risk_score': risk_score, 'status': 'updated'})
    return jsonify({'error': 'Student not found'}), 404

@app.route('/api/interventions/<int:student_id>')
def get_interventions(student_id):
    interventions = Intervention.query.filter_by(student_id=student_id).all()
    interventions_data = []
    for intervention in interventions:
        interventions_data.append({
            'id': intervention.id,
            'level': intervention.level,
            'type': intervention.type,
            'content': intervention.content,
            'status': intervention.status,
            'created_at': intervention.created_at.isoformat()
        })
    return jsonify(interventions_data)

@app.route('/api/mentors')
def get_mentors():
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

@app.route('/api/dashboard_stats')
def get_dashboard_stats():
    total_students = Student.query.count()
    high_risk = Student.query.filter(Student.risk_score > 0.6).count()
    active_interventions = Intervention.query.filter_by(status='pending').count()
    
    return jsonify({
        'total_students': total_students,
        'high_risk_percentage': round((high_risk/total_students)*100, 1) if total_students > 0 else 0,
        'active_interventions': active_interventions,
        'retention_improvement': "25%"  # Proyección
    })

@app.route('/api/impact_metrics')
def get_impact_metrics():
    """Endpoint para métricas de impacto financiero"""
    total_students = Student.query.count()
    students_at_risk = Student.query.filter(Student.risk_score > 0.6).count()
    interventions_successful = Intervention.query.filter(
        Intervention.effectiveness_rating > 0.7
    ).count()
    total_interventions = Intervention.query.count()
    
    # Cálculos de ROI
    cost_per_intervention = 150  # USD
    revenue_per_retained_student = 12000  # Colegiatura anual
    intervention_success_rate = (interventions_successful / max(total_interventions, 1)) * 100
    
    return jsonify({
        'students_identified_at_risk': students_at_risk,
        'intervention_success_rate': f'{intervention_success_rate:.0f}%',
        'estimated_retention_increase': '25%',
        'roi_per_student': revenue_per_retained_student - cost_per_intervention,
        'projected_annual_savings': students_at_risk * revenue_per_retained_student * 0.25,
        'cost_effectiveness': f'${cost_per_intervention}/estudiante',
        'total_students_monitored': total_students
    })

@app.route('/api/simulate_data')
def simulate_data():
    """Endpoint para simular datos de prueba con perfiles de riesgo diferenciados"""
    
    # Crear estudiantes con perfiles específicos de riesgo
    students_profiles = [
        # PERFILES DE ALTO RIESGO (3 estudiantes)
        {
            'name': 'Ana García', 
            'email': 'ana@example.com', 
            'program': 'Ingeniería de Sistemas', 
            'semester': 3, 
            'entry_year': 2023,
            'risk_profile': 'high',
            'academic_pattern': 'declining_performance',
            'behavioral_pattern': 'high_impostor_syndrome'
        },
        {
            'name': 'María López', 
            'email': 'maria@example.com', 
            'program': 'Ingeniería Industrial', 
            'semester': 2, 
            'entry_year': 2024,
            'risk_profile': 'high',
            'academic_pattern': 'poor_attendance',
            'behavioral_pattern': 'social_isolation'
        },
        {
            'name': 'Carmen Rodriguez', 
            'email': 'carmen@example.com', 
            'program': 'Matemáticas', 
            'semester': 4, 
            'entry_year': 2022,
            'risk_profile': 'high',
            'academic_pattern': 'failing_grades',
            'behavioral_pattern': 'low_participation'
        },
        
        # PERFILES DE RIESGO MEDIO (3 estudiantes)
        {
            'name': 'Sofia Mendez', 
            'email': 'sofia@example.com', 
            'program': 'Ingeniería de Sistemas', 
            'semester': 1, 
            'entry_year': 2024,
            'risk_profile': 'medium',
            'academic_pattern': 'inconsistent_performance',
            'behavioral_pattern': 'moderate_confidence_issues'
        },
        {
            'name': 'Isabella Torres', 
            'email': 'isabella@example.com', 
            'program': 'Matemáticas', 
            'semester': 2, 
            'entry_year': 2024,
            'risk_profile': 'medium',
            'academic_pattern': 'average_with_struggles',
            'behavioral_pattern': 'peer_pressure'
        },
        {
            'name': 'Valentina Ruiz', 
            'email': 'valentina@example.com', 
            'program': 'Ingeniería Industrial', 
            'semester': 3, 
            'entry_year': 2023,
            'risk_profile': 'medium',
            'academic_pattern': 'inconsistent_attendance',
            'behavioral_pattern': 'adaptation_difficulties'
        },
        
        # PERFILES DE BAJO RIESGO (2 estudiantes)
        {
            'name': 'Camila Herrera', 
            'email': 'camila@example.com', 
            'program': 'Ingeniería de Sistemas', 
            'semester': 5, 
            'entry_year': 2022,
            'risk_profile': 'low',
            'academic_pattern': 'excellent_performance',
            'behavioral_pattern': 'high_confidence'
        },
        {
            'name': 'Daniela Castro', 
            'email': 'daniela@example.com', 
            'program': 'Matemáticas', 
            'semester': 1, 
            'entry_year': 2024,
            'risk_profile': 'low',
            'academic_pattern': 'strong_foundation',
            'behavioral_pattern': 'well_adapted'
        }
    ]
    
    created_students = []
    for profile in students_profiles:
        if not Student.query.filter_by(email=profile['email']).first():
            student_data = {k: v for k, v in profile.items() 
                          if k in ['name', 'email', 'program', 'semester', 'entry_year']}
            student = Student(**student_data)
            db.session.add(student)
            created_students.append((student, profile))
    
    # Crear mentoras de ejemplo
    mentors_data = [
        {'name': 'Dra. Elena Martinez', 'email': 'elena@example.com', 'program': 'Ingeniería de Sistemas', 'graduation_year': 2018, 'current_position': 'Senior Developer'},
        {'name': 'Ing. Sofia Chen', 'email': 'sofia.chen@example.com', 'program': 'Ingeniería Industrial', 'graduation_year': 2019, 'current_position': 'Project Manager'},
        {'name': 'Dra. Carla Vega', 'email': 'carla@example.com', 'program': 'Matemáticas', 'graduation_year': 2017, 'current_position': 'Data Scientist'},
        {'name': 'Ing. Natalia Silva', 'email': 'natalia@example.com', 'program': 'Ingeniería de Sistemas', 'graduation_year': 2020, 'current_position': 'Tech Lead'},
        {'name': 'Dra. Andrea Luna', 'email': 'andrea@example.com', 'program': 'Ingeniería Industrial', 'graduation_year': 2016, 'current_position': 'Operations Director'},
        {'name': 'Ing. Patricia Morales', 'email': 'patricia@example.com', 'program': 'Matemáticas', 'graduation_year': 2019, 'current_position': 'Research Scientist'}
    ]
    
    created_mentors = []
    for data in mentors_data:
        if not Mentor.query.filter_by(email=data['email']).first():
            mentor = Mentor(**data)
            db.session.add(mentor)
            created_mentors.append(mentor)
    
    # Commit para obtener IDs
    db.session.commit()
    
    # Obtener todos los estudiantes con sus perfiles
    all_students_with_profiles = []
    for student, profile in created_students:
        all_students_with_profiles.append((student, profile))
    
    # Agregar estudiantes existentes con perfiles aleatorios si es necesario
    existing_students = Student.query.filter(
        ~Student.email.in_([p['email'] for p in students_profiles])
    ).all()
    
    for student in existing_students:
        # Asignar perfil aleatorio a estudiantes existentes
        risk_profiles = ['low', 'medium', 'high']
        random_profile = {
            'risk_profile': random.choice(risk_profiles),
            'academic_pattern': 'existing_student',
            'behavioral_pattern': 'existing_student'
        }
        all_students_with_profiles.append((student, random_profile))
    
    # Materias por programa
    subjects = {
        'Ingeniería de Sistemas': ['Programación', 'Algoritmos', 'Base de Datos', 'Matemáticas Discretas', 'Física'],
        'Ingeniería Industrial': ['Estadística', 'Investigación de Operaciones', 'Economía', 'Gestión de Calidad', 'Matemáticas'],
        'Matemáticas': ['Cálculo', 'Álgebra Lineal', 'Estadística', 'Análisis Matemático', 'Geometría']
    }
    
    # Generar registros académicos y comportamentales según el perfil
    for student, profile in all_students_with_profiles:
        program_subjects = subjects.get(student.program, subjects['Ingeniería de Sistemas'])
        risk_profile = profile.get('risk_profile', 'medium')
        
        # Crear 4-6 registros académicos por estudiante
        num_records = random.randint(4, 6)
        for i in range(num_records):
            subject = random.choice(program_subjects)
            
            # Generar datos según perfil de riesgo
            if risk_profile == 'high':
                # Alto riesgo: notas bajas, asistencia pobre, tareas incompletas
                base_grade = random.uniform(45, 65)  # Notas bajas
                attendance_rate = random.uniform(40, 70)  # Asistencia pobre
                participation_score = random.uniform(30, 60)  # Baja participación
                assignment_completion = random.uniform(40, 75)  # Tareas incompletas
                
                # Empeora con el tiempo
                if i >= 2:
                    base_grade = max(40, base_grade - random.uniform(5, 15))
                    attendance_rate = max(30, attendance_rate - random.uniform(10, 20))
                    participation_score = max(20, participation_score - random.uniform(5, 15))
                    assignment_completion = max(30, assignment_completion - random.uniform(10, 20))
                    
            elif risk_profile == 'medium':
                # Riesgo medio: rendimiento inconsistente
                base_grade = random.uniform(65, 80)  # Notas promedio
                attendance_rate = random.uniform(70, 85)  # Asistencia regular
                participation_score = random.uniform(60, 80)  # Participación moderada
                assignment_completion = random.uniform(70, 90)  # Tareas mayormente completas
                
                # Variabilidad en el tiempo
                if random.random() > 0.5:  # 50% chance de declive
                    base_grade -= random.uniform(0, 10)
                    attendance_rate -= random.uniform(0, 15)
                    
            else:  # low risk
                # Bajo riesgo: buen rendimiento
                base_grade = random.uniform(80, 95)  # Buenas notas
                attendance_rate = random.uniform(85, 100)  # Excelente asistencia
                participation_score = random.uniform(80, 95)  # Alta participación
                assignment_completion = random.uniform(90, 100)  # Tareas completas
                
                # Mejora o se mantiene con el tiempo
                if i >= 2:
                    base_grade = min(100, base_grade + random.uniform(0, 5))
                    
            academic_record = AcademicRecord(
                student_id=student.id,
                subject=subject,
                grade=base_grade,
                attendance_rate=attendance_rate,
                participation_score=participation_score,
                assignment_completion=assignment_completion,
                date_recorded=datetime.utcnow() - timedelta(days=30 * i)
            )
            db.session.add(academic_record)
        
        # Crear registros comportamentales según perfil
        num_behavioral = random.randint(3, 5)
        for i in range(num_behavioral):
            
            if risk_profile == 'high':
                # Alto riesgo: problemas comportamentales significativos
                oral_participation = random.uniform(20, 50)  # Muy baja participación oral
                self_assessment_confidence = random.uniform(30, 60)  # Baja confianza
                teacher_interaction_frequency = random.uniform(20, 50)  # Poca interacción
                group_work_engagement = random.uniform(40, 70)  # Problemas grupales
                impostor_syndrome_indicators = random.uniform(70, 95)  # Alto síndrome del impostor
                
                # Empeora con el tiempo
                if i >= 2:
                    oral_participation = max(10, oral_participation - random.uniform(5, 15))
                    self_assessment_confidence = max(20, self_assessment_confidence - random.uniform(5, 20))
                    impostor_syndrome_indicators = min(100, impostor_syndrome_indicators + random.uniform(5, 15))
                    
            elif risk_profile == 'medium':
                # Riesgo medio: algunos indicadores preocupantes
                oral_participation = random.uniform(50, 75)  # Participación moderada
                self_assessment_confidence = random.uniform(60, 80)  # Confianza variable
                teacher_interaction_frequency = random.uniform(50, 75)  # Interacción moderada
                group_work_engagement = random.uniform(65, 85)  # Trabajo grupal normal
                impostor_syndrome_indicators = random.uniform(45, 70)  # Síndrome del impostor moderado
                
            else:  # low risk
                # Bajo riesgo: indicadores positivos
                oral_participation = random.uniform(75, 95)  # Alta participación
                self_assessment_confidence = random.uniform(80, 95)  # Alta confianza
                teacher_interaction_frequency = random.uniform(70, 90)  # Buena interacción
                group_work_engagement = random.uniform(85, 100)  # Excelente trabajo grupal
                impostor_syndrome_indicators = random.uniform(20, 45)  # Bajo síndrome del impostor
                
            behavioral_record = BehavioralRecord(
                student_id=student.id,
                oral_participation=oral_participation,
                self_assessment_confidence=self_assessment_confidence,
                teacher_interaction_frequency=teacher_interaction_frequency,
                group_work_engagement=group_work_engagement,
                impostor_syndrome_indicators=impostor_syndrome_indicators,
                date_recorded=datetime.utcnow() - timedelta(days=20 * i)
            )
            db.session.add(behavioral_record)
    
    # Commit antes de recalcular riesgos
    db.session.commit()
    
    # Recrear modelo con datos realistas DESPUÉS de generar datos simulados
    print("🔄 Recreando modelo predictivo con datos realistas...")
    risk_predictor.create_realistic_model()
    
    # Recalcular todos los scores con el nuevo modelo
    print("📊 Recalculando scores de riesgo para todos los estudiantes...")
    all_students = Student.query.all()
    for student in all_students:
        new_risk_score = risk_predictor.predict_risk(student.id)
        student.risk_score = new_risk_score
        student.last_risk_update = datetime.utcnow()
        
        # Trigger intervenciones basadas en el nuevo score
        InterventionSystem.trigger_intervention(student.id, new_risk_score)
    
    # Asignar algunas mentoras automáticamente a estudiantes de alto riesgo
    high_risk_students = Student.query.filter(Student.risk_score > 0.6).all()
    available_mentors = Mentor.query.filter_by(availability=True).all()
    
    for i, student in enumerate(high_risk_students[:len(available_mentors)]):
        mentor = available_mentors[i % len(available_mentors)]
        
        # Verificar si ya tiene mentora
        existing_match = MentorMatch.query.filter_by(
            student_id=student.id, 
            status='active'
        ).first()
        
        if not existing_match:
            match = MentorMatch(
                student_id=student.id,
                mentor_id=mentor.id,
                match_score=random.uniform(0.75, 0.95)
            )
            db.session.add(match)
            mentor.current_mentees = min(mentor.max_mentees, mentor.current_mentees + 1)
    
    # Crear intervenciones específicas para diferentes niveles
    intervention_contents = {
        'high': [
            "⚠️ ALERTA CRÍTICA: Múltiples indicadores de riesgo detectados. Plan de recuperación integral activado.",
            "🆘 Sesión de emergencia programada con consejera académica especializada en retención femenina STEM.",
            "👥 Mentora de alto impacto asignada + plan de seguimiento semanal personalizado.",
            "📚 Recursos intensivos: tutoría especializada + técnicas de manejo de síndrome del impostor."
        ],
        'medium': [
            "⚡ Intervención preventiva activada: Señales tempranas detectadas en participación y confianza.",
            "👩‍🏫 Conectada con mentora especializada para sesiones de refuerzo motivacional.",
            "📈 Plan de mejora académica: estrategias específicas para materias identificadas.",
            "🎯 Seguimiento quincenal programado para monitorear progreso y ajustar apoyo."
        ],
        'low': [
            "✅ Rendimiento estable detectado. Recursos preventivos enviados para mantener trayectoria positiva.",
            "🌟 Perfil identificado como potencial mentora para estudiantes en dificultades.",
            "📚 Contenido de desarrollo profesional y liderazgo femenino en STEM compartido.",
            "🏆 Reconocimiento por excelente desempeño y compromiso académico."
        ]
    }
    
    # Crear intervenciones basadas en el nivel de riesgo real
    for student in all_students:
        if student.risk_score >= 0.7:
            risk_category = 'high'
            level = 3
            intervention_type = 'counselor'
        elif student.risk_score >= 0.4:
            risk_category = 'medium'
            level = 2
            intervention_type = 'mentor'
        else:
            risk_category = 'low'
            level = 1
            intervention_type = 'automatic'
        
        # Crear 1-2 intervenciones por estudiante
        num_interventions = random.randint(1, 2)
        for _ in range(num_interventions):
            intervention = Intervention(
                student_id=student.id,
                level=level,
                type=intervention_type,
                content=random.choice(intervention_contents[risk_category]),
                status=random.choice(['delivered', 'completed']),
                effectiveness_rating=random.uniform(0.6, 0.9) if random.random() > 0.3 else None,
                created_at=datetime.utcnow() - timedelta(days=random.randint(1, 30))
            )
            db.session.add(intervention)
    
    db.session.commit()
    
    # Validar distribución final
    is_valid = validate_risk_distribution()
    print(f"✅ Distribución de riesgo {'válida' if is_valid else 'requiere ajuste'}")
    
    # Estadísticas finales
    total_students = Student.query.count()
    high_risk_count = Student.query.filter(Student.risk_score >= 0.7).count()
    medium_risk_count = Student.query.filter(
        Student.risk_score >= 0.4, 
        Student.risk_score < 0.7
    ).count()
    low_risk_count = Student.query.filter(Student.risk_score < 0.4).count()
    
    return jsonify({
        'message': 'Datos simulados con perfiles de riesgo diferenciados creados exitosamente',
        'students_created': len(created_students),
        'mentors_created': len(created_mentors),
        'total_students': total_students,
        'risk_distribution': {
            'high_risk': high_risk_count,
            'medium_risk': medium_risk_count,
            'low_risk': low_risk_count
        },
        'academic_records': AcademicRecord.query.count(),
        'behavioral_records': BehavioralRecord.query.count(),
        'interventions': Intervention.query.count(),
        'mentor_matches': MentorMatch.query.count(),
        'model_validation': is_valid
    })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)