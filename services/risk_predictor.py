import numpy as np
from sklearn.ensemble import RandomForestClassifier
import joblib
from models import Student, AcademicRecord, BehavioralRecord
from config import Config

class RiskPredictor:
    def __init__(self):
        self.model = None
        self.config = Config.RISK_CONFIG
        self.use_rule_based = self.config['USE_RULE_BASED']
        self.load_or_create_model()
    
    def load_or_create_model(self):
        """Cargar modelo existente o crear uno nuevo"""
        try:
            self.model = joblib.load(self.config['MODEL_PATH'])
            if not self.validate_model():
                self.create_realistic_model()
        except:
            self.create_realistic_model()
    
    def validate_model(self):
        """Verificar que el modelo produce resultados coherentes"""
        try:
            # Datos de prueba: estudiante de alto riesgo
            high_risk_features = np.array([[45, 50, 30, 60, 25, 40, 30, 85]])
            # Datos de prueba: estudiante de bajo riesgo  
            low_risk_features = np.array([[90, 95, 85, 95, 90, 88, 85, 25]])
            
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
        joblib.dump(self.model, self.config['MODEL_PATH'])
        
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
                grade = np.random.normal(65, 10)
                attendance_rate = np.random.normal(60, 15)
                participation_score = np.random.normal(40, 10)
                assignment_completion = np.random.normal(70, 15)
                
                # Variables comportamentales críticas para mujeres
                oral_participation = np.random.normal(30, 10)
                self_assessment_confidence = np.random.normal(45, 10)
                teacher_interaction_frequency = np.random.normal(35, 10)
                impostor_syndrome_indicators = np.random.normal(80, 10)
                
                label = 1  # Alto riesgo
                
            elif risk_profile == 'medium':
                # RIESGO MEDIO: Estudiantes en punto de inflexión
                grade = np.random.normal(75, 8)
                attendance_rate = np.random.normal(75, 10)
                participation_score = np.random.normal(60, 12)
                assignment_completion = np.random.normal(80, 10)
                
                oral_participation = np.random.normal(55, 15)
                self_assessment_confidence = np.random.normal(65, 12)
                teacher_interaction_frequency = np.random.normal(60, 15)
                impostor_syndrome_indicators = np.random.normal(55, 15)
                
                # 40% probabilidad de ser clasificado como riesgo
                label = 1 if np.random.random() < 0.4 else 0
                
            else:  # low risk
                # BAJO RIESGO: Estudiantes exitosas
                grade = np.random.normal(85, 8)
                attendance_rate = np.random.normal(90, 5)
                participation_score = np.random.normal(85, 8)
                assignment_completion = np.random.normal(92, 5)
                
                oral_participation = np.random.normal(80, 10)
                self_assessment_confidence = np.random.normal(85, 8)
                teacher_interaction_frequency = np.random.normal(80, 10)
                impostor_syndrome_indicators = np.random.normal(30, 10)
                
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
        academic = AcademicRecord.query.filter_by(
            student_id=student_id
        ).order_by(AcademicRecord.date_recorded.desc()).first()
        
        behavioral = BehavioralRecord.query.filter_by(
            student_id=student_id
        ).order_by(BehavioralRecord.date_recorded.desc()).first()
        
        if not academic or not behavioral:
            return 0.0
        
        if self.use_rule_based:
            return self.calculate_risk_rule_based(academic, behavioral)
        else:
            return self.calculate_risk_ml_based(academic, behavioral)
    
    def calculate_risk_rule_based(self, academic, behavioral):
        """Sistema de scoring basado en reglas específicas para mujeres en STEM"""
        risk_score = 0.0
        weights = self.config['WEIGHTS']
        
        # 1. Rendimiento académico
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
        
        # 2. Asistencia
        attendance_rate = academic.attendance_rate or 0
        if attendance_rate < 70:
            attendance_risk = 0.9
        elif attendance_rate < 80:
            attendance_risk = 0.6
        elif attendance_rate < 90:
            attendance_risk = 0.3
        else:
            attendance_risk = 0.1
        
        # 3. Factores comportamentales críticos para mujeres
        behavioral_risk = 0
        
        # Síndrome del impostor (peso mayor)
        impostor_syndrome = behavioral.impostor_syndrome_indicators or 0
        if impostor_syndrome > 75:
            behavioral_risk += 0.4
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
    
    def get_risk_factors(self, student_id):
        """Obtener factores específicos que contribuyen al riesgo"""
        student = Student.query.get(student_id)
        if not student:
            return {}
        
        academic = AcademicRecord.query.filter_by(
            student_id=student_id
        ).order_by(AcademicRecord.date_recorded.desc()).first()
        
        behavioral = BehavioralRecord.query.filter_by(
            student_id=student_id
        ).order_by(BehavioralRecord.date_recorded.desc()).first()
        
        if not academic or not behavioral:
            return {}
        
        factors = {
            'academic': {
                'grade': academic.grade or 0,
                'attendance_rate': academic.attendance_rate or 0,
                'assignment_completion': academic.assignment_completion or 0,
                'risk_level': 'low'
            },
            'behavioral': {
                'oral_participation': behavioral.oral_participation or 0,
                'self_confidence': behavioral.self_assessment_confidence or 0,
                'impostor_syndrome': behavioral.impostor_syndrome_indicators or 0,
                'teacher_interaction': behavioral.teacher_interaction_frequency or 0,
                'risk_level': 'low'
            },
            'primary_concerns': []
        }
        
        # Identificar preocupaciones principales
        if (academic.grade or 0) < 70:
            factors['primary_concerns'].append('Rendimiento académico bajo')
            factors['academic']['risk_level'] = 'high'
        
        if (academic.attendance_rate or 0) < 80:
            factors['primary_concerns'].append('Asistencia irregular')
        
        if (behavioral.impostor_syndrome_indicators or 0) > 70:
            factors['primary_concerns'].append('Alto síndrome del impostor')
            factors['behavioral']['risk_level'] = 'high'
        
        if (behavioral.oral_participation or 0) < 50:
            factors['primary_concerns'].append('Baja participación oral')
            factors['behavioral']['risk_level'] = 'high'
        
        if (behavioral.self_assessment_confidence or 0) < 60:
            factors['primary_concerns'].append('Baja autoconfianza')
        
        return factors