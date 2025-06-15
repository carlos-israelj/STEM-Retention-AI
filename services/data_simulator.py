import random
from datetime import datetime, timedelta
from models import (
    Student, Mentor, AcademicRecord, BehavioralRecord, 
    Intervention, MentorMatch, SupportRequest, SupportResponse, db
)
from services.support_services import SupportPrioritizer

class DataSimulator:
    """Servicio para simular datos de prueba del sistema"""
    
    def __init__(self):
        self.programs = ['Ingeniería de Sistemas', 'Ingeniería Industrial', 'Matemáticas']
        self.subjects = {
            'Ingeniería de Sistemas': ['Programación', 'Algoritmos', 'Base de Datos', 'Matemáticas Discretas', 'Física'],
            'Ingeniería Industrial': ['Estadística', 'Investigación de Operaciones', 'Economía', 'Gestión de Calidad', 'Matemáticas'],
            'Matemáticas': ['Cálculo', 'Álgebra Lineal', 'Estadística', 'Análisis Matemático', 'Geometría']
        }
    
    def simulate_complete_system(self):
        """Simular datos completos del sistema incluyendo apoyo estudiantil"""
        try:
            print("🔄 Iniciando simulación completa del sistema...")
            
            # Simular estudiantes
            students_result = self.simulate_students()
            
            # Simular mentoras
            mentors_result = self.simulate_mentors()
            
            # Simular sistema de apoyo
            support_result = self.simulate_support_system()
            
            # Recrear modelo predictivo
            self.recreate_risk_model()
            
            # Recalcular riesgos y crear intervenciones
            self.recalculate_risks_and_interventions()
            
            # Asignar mentoras
            self.assign_mentors()
            
            # Validar distribución
            is_valid = self.validate_risk_distribution()
            
            # Estadísticas finales
            final_stats = self.get_final_statistics()
            
            print("✅ Simulación completa finalizada")
            
            return {
                'success': True,
                'message': 'Datos completos simulados exitosamente (estudiantes + sistema de apoyo)',
                'students': students_result,
                'mentors': mentors_result,
                'support_system': support_result,
                'final_statistics': final_stats,
                'model_validation': is_valid
            }
            
        except Exception as e:
            print(f"Error en simulación completa: {e}")
            return {'success': False, 'error': str(e)}
    
    def simulate_students(self):
        """Simular estudiantes con perfiles específicos de riesgo"""
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
        
        # Commit para obtener IDs
        db.session.commit()
        
        # Generar registros académicos y comportamentales
        self.generate_academic_behavioral_records(created_students)
        
        return {
            'created': len(created_students),
            'total': Student.query.count()
        }
    
    def simulate_mentors(self):
        """Simular mentoras"""
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
        
        db.session.commit()
        
        return {
            'created': len(created_mentors),
            'total': Mentor.query.count()
        }
    
    def simulate_support_system(self):
        """Simular sistema de apoyo estudiantil"""
        return create_sample_support_data()
    
    def generate_academic_behavioral_records(self, students_with_profiles):
        """Generar registros académicos y comportamentales según perfiles"""
        for student, profile in students_with_profiles:
            program_subjects = self.subjects.get(student.program, self.subjects['Ingeniería de Sistemas'])
            risk_profile = profile.get('risk_profile', 'medium')
            
            # Crear 4-6 registros académicos por estudiante
            num_records = random.randint(4, 6)
            for i in range(num_records):
                subject = random.choice(program_subjects)
                academic_data = self.generate_academic_data(risk_profile, i)
                
                academic_record = AcademicRecord(
                    student_id=student.id,
                    subject=subject,
                    grade=academic_data['grade'],
                    attendance_rate=academic_data['attendance_rate'],
                    participation_score=academic_data['participation_score'],
                    assignment_completion=academic_data['assignment_completion'],
                    date_recorded=datetime.utcnow() - timedelta(days=30 * i)
                )
                db.session.add(academic_record)
            
            # Crear registros comportamentales
            num_behavioral = random.randint(3, 5)
            for i in range(num_behavioral):
                behavioral_data = self.generate_behavioral_data(risk_profile, i)
                
                behavioral_record = BehavioralRecord(
                    student_id=student.id,
                    oral_participation=behavioral_data['oral_participation'],
                    self_assessment_confidence=behavioral_data['self_assessment_confidence'],
                    teacher_interaction_frequency=behavioral_data['teacher_interaction_frequency'],
                    group_work_engagement=behavioral_data['group_work_engagement'],
                    impostor_syndrome_indicators=behavioral_data['impostor_syndrome_indicators'],
                    date_recorded=datetime.utcnow() - timedelta(days=20 * i)
                )
                db.session.add(behavioral_record)
        
        db.session.commit()
    
    def generate_academic_data(self, risk_profile, time_index):
        """Generar datos académicos según perfil de riesgo"""
        if risk_profile == 'high':
            base_grade = random.uniform(45, 65)
            attendance_rate = random.uniform(40, 70)
            participation_score = random.uniform(30, 60)
            assignment_completion = random.uniform(40, 75)
            
            # Empeora con el tiempo
            if time_index >= 2:
                base_grade = max(40, base_grade - random.uniform(5, 15))
                attendance_rate = max(30, attendance_rate - random.uniform(10, 20))
                participation_score = max(20, participation_score - random.uniform(5, 15))
                assignment_completion = max(30, assignment_completion - random.uniform(10, 20))
                
        elif risk_profile == 'medium':
            base_grade = random.uniform(65, 80)
            attendance_rate = random.uniform(70, 85)
            participation_score = random.uniform(60, 80)
            assignment_completion = random.uniform(70, 90)
            
            # Variabilidad en el tiempo
            if random.random() > 0.5:
                base_grade -= random.uniform(0, 10)
                attendance_rate -= random.uniform(0, 15)
                
        else:  # low risk
            base_grade = random.uniform(80, 95)
            attendance_rate = random.uniform(85, 100)
            participation_score = random.uniform(80, 95)
            assignment_completion = random.uniform(90, 100)
            
            # Mejora o se mantiene
            if time_index >= 2:
                base_grade = min(100, base_grade + random.uniform(0, 5))
        
        return {
            'grade': base_grade,
            'attendance_rate': attendance_rate,
            'participation_score': participation_score,
            'assignment_completion': assignment_completion
        }
    
    def generate_behavioral_data(self, risk_profile, time_index):
        """Generar datos comportamentales según perfil de riesgo"""
        if risk_profile == 'high':
            oral_participation = random.uniform(20, 50)
            self_assessment_confidence = random.uniform(30, 60)
            teacher_interaction_frequency = random.uniform(20, 50)
            group_work_engagement = random.uniform(40, 70)
            impostor_syndrome_indicators = random.uniform(70, 95)
            
            # Empeora con el tiempo
            if time_index >= 2:
                oral_participation = max(10, oral_participation - random.uniform(5, 15))
                self_assessment_confidence = max(20, self_assessment_confidence - random.uniform(5, 20))
                impostor_syndrome_indicators = min(100, impostor_syndrome_indicators + random.uniform(5, 15))
                
        elif risk_profile == 'medium':
            oral_participation = random.uniform(50, 75)
            self_assessment_confidence = random.uniform(60, 80)
            teacher_interaction_frequency = random.uniform(50, 75)
            group_work_engagement = random.uniform(65, 85)
            impostor_syndrome_indicators = random.uniform(45, 70)
            
        else:  # low risk
            oral_participation = random.uniform(75, 95)
            self_assessment_confidence = random.uniform(80, 95)
            teacher_interaction_frequency = random.uniform(70, 90)
            group_work_engagement = random.uniform(85, 100)
            impostor_syndrome_indicators = random.uniform(20, 45)
        
        return {
            'oral_participation': oral_participation,
            'self_assessment_confidence': self_assessment_confidence,
            'teacher_interaction_frequency': teacher_interaction_frequency,
            'group_work_engagement': group_work_engagement,
            'impostor_syndrome_indicators': impostor_syndrome_indicators
        }
    
    def recreate_risk_model(self):
        """Recrear modelo predictivo con datos realistas"""
        try:
            # Importación dentro de la función para evitar importación circular
            from services.risk_predictor import RiskPredictor
            print("🔄 Recreando modelo predictivo con datos realistas...")
            predictor = RiskPredictor()
            predictor.create_realistic_model()
        except Exception as e:
            print(f"Error recreando modelo: {e}")
    
    def recalculate_risks_and_interventions(self):
        """Recalcular riesgos y crear intervenciones"""
        try:
            # Importaciones dentro de la función para evitar importación circular
            from services.risk_predictor import RiskPredictor
            
            print("📊 Recalculando scores de riesgo para todos los estudiantes...")
            
            predictor = RiskPredictor()
            all_students = Student.query.all()
            
            for student in all_students:
                new_risk_score = predictor.predict_risk(student.id)
                student.risk_score = new_risk_score
                student.last_risk_update = datetime.utcnow()
                
                # Crear intervenciones manualmente para evitar importación circular
                self.create_simple_intervention(student, new_risk_score)
            
            db.session.commit()
            
        except Exception as e:
            print(f"Error recalculando riesgos: {e}")
    
    def create_simple_intervention(self, student, risk_score):
        """Crear intervención simple sin dependencias circulares"""
        try:
            # Determinar nivel de intervención
            if risk_score < 0.3:
                level = 0  # Sin intervención
                return
            elif risk_score < 0.6:
                level = 1  # Recursos automáticos
                intervention_type = 'automatic'
                content = f"Recursos automáticos enviados para {student.name}. Score de riesgo: {risk_score:.2f}"
            elif risk_score < 0.8:
                level = 2  # Conexión con mentora
                intervention_type = 'mentor'
                content = f"Asignación de mentora programada para {student.name}. Score de riesgo: {risk_score:.2f}"
            else:
                level = 3  # Alerta a consejeros
                intervention_type = 'counselor'
                content = f"Alerta crítica para {student.name}. Score de riesgo: {risk_score:.2f}. Intervención inmediata requerida."
            
            # Solo crear nueva intervención si el nivel cambió
            if student.intervention_level != level:
                student.intervention_level = level
                
                intervention = Intervention(
                    student_id=student.id,
                    level=level,
                    type=intervention_type,
                    content=content,
                    status='pending'
                )
                db.session.add(intervention)
                
        except Exception as e:
            print(f"Error creando intervención simple: {e}")
    
    def assign_mentors(self):
        """Asignar mentoras a estudiantes de alto riesgo"""
        try:
            high_risk_students = Student.query.filter(Student.risk_score > 0.6).all()
            available_mentors = Mentor.query.filter_by(availability=True).all()
            
            if not available_mentors:
                print("⚠️ No hay mentoras disponibles")
                return
            
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
            
            db.session.commit()
            print(f"✅ Mentoras asignadas a {len(high_risk_students)} estudiantes de alto riesgo")
            
        except Exception as e:
            print(f"Error asignando mentoras: {e}")
    
    def validate_risk_distribution(self):
        """Validar que la distribución de riesgo sea realista"""
        try:
            students = Student.query.all()
            if not students:
                return False
                
            risk_distribution = {'low': 0, 'medium': 0, 'high': 0}
            
            for student in students:
                if student.risk_score < 0.4:
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
            
        except Exception as e:
            print(f"Error validando distribución: {e}")
            return False
    
    def get_final_statistics(self):
        """Obtener estadísticas finales del sistema"""
        try:
            total_students = Student.query.count()
            high_risk_count = Student.query.filter(Student.risk_score >= 0.7).count()
            medium_risk_count = Student.query.filter(
                Student.risk_score >= 0.4, 
                Student.risk_score < 0.7
            ).count()
            low_risk_count = Student.query.filter(Student.risk_score < 0.4).count()
            
            return {
                'students': {
                    'total': total_students,
                    'high_risk': high_risk_count,
                    'medium_risk': medium_risk_count,
                    'low_risk': low_risk_count
                },
                'records': {
                    'academic_records': AcademicRecord.query.count(),
                    'behavioral_records': BehavioralRecord.query.count(),
                    'interventions': Intervention.query.count(),
                    'mentor_matches': MentorMatch.query.count()
                },
                'support_system': {
                    'support_requests': SupportRequest.query.count(),
                    'support_responses': SupportResponse.query.count()
                }
            }
            
        except Exception as e:
            print(f"Error obteniendo estadísticas: {e}")
            return {}

# Función independiente para crear datos de apoyo
def create_sample_support_data():
    """Crear datos de ejemplo para el sistema de apoyo"""
    try:
        sample_requests = [
            {
                'anonymous': False,
                'student_name': 'Andrea Vásquez',
                'student_email': 'andrea@universidad.edu',
                'urgency': 'high',
                'category': 'emotional',
                'message': 'Me siento muy abrumada con todas las materias. Siento que no soy lo suficientemente inteligente para estar en ingeniería. Todos mis compañeros parecen entender todo tan fácilmente y yo lucho constantemente. He pensado en cambiarme de carrera pero no sé qué hacer.',
                'previous_help': 'Intenté hablar con mi profesora de cálculo pero no me sintió muy cómoda.',
                'contact_preference': 'email'
            },
            {
                'anonymous': True,
                'student_name': None,
                'student_email': None,
                'urgency': 'medium',
                'category': 'academic',
                'message': 'Estoy teniendo muchas dificultades con programación. Siento que todos en mi clase ya saben programar y yo apenas estoy empezando. ¿Pueden ayudarme con recursos adicionales o tutorías?',
                'previous_help': None,
                'contact_preference': 'no-contact'
            },
            {
                'anonymous': False,
                'student_name': 'Camila Herrera',
                'student_email': 'camila@universidad.edu',
                'urgency': 'low',
                'category': 'career',
                'message': 'Me gustaría orientación sobre qué especialización elegir en ingeniería de sistemas. También me interesa saber sobre oportunidades de prácticas profesionales.',
                'previous_help': 'Asistí a una charla vocacional el semestre pasado.',
                'contact_preference': 'in-person'
            },
            {
                'anonymous': True,
                'student_name': None,
                'student_email': 'anonima@temp.edu',
                'urgency': 'high',
                'category': 'social',
                'message': 'Me siento muy sola en el programa. Parece que todos ya tienen sus grupos de amigos y yo no logro conectar con nadie. A veces siento que no pertenezco aquí. Vengo de un pueblo pequeño y todo esto es muy diferente a lo que estoy acostumbrada.',
                'previous_help': 'No he buscado ayuda antes, me da pena.',
                'contact_preference': 'email'
            },
            {
                'anonymous': False,
                'student_name': 'Sofia Mendez',
                'student_email': 'sofia@universidad.edu',
                'urgency': 'medium',
                'category': 'financial',
                'message': 'Estoy teniendo problemas económicos y no sé si podré continuar con mis estudios. ¿Existen becas o programas de apoyo financiero para estudiantes de matemáticas?',
                'previous_help': 'Hablé con la oficina de registro pero no me dieron mucha información.',
                'contact_preference': 'phone'
            }
        ]
        
        created_requests = 0
        for req_data in sample_requests:
            # Verificar si ya existe una solicitud similar
            existing = None
            if req_data['student_email']:
                existing = SupportRequest.query.filter_by(
                    student_email=req_data['student_email']
                ).first()
            
            if not existing:
                priority_score = SupportPrioritizer.calculate_priority_score(req_data)
                
                support_request = SupportRequest(
                    anonymous=req_data['anonymous'],
                    student_name=req_data['student_name'],
                    student_email=req_data['student_email'],
                    urgency=req_data['urgency'],
                    category=req_data['category'],
                    message=req_data['message'],
                    previous_help=req_data['previous_help'],
                    contact_preference=req_data['contact_preference'],
                    priority_score=priority_score,
                    status='pending',
                    created_at=datetime.utcnow() - timedelta(
                        days=random.randint(0, 7),
                        hours=random.randint(0, 23)
                    )
                )
                
                db.session.add(support_request)
                created_requests += 1
        
        db.session.commit()
        
        # Crear algunas respuestas de ejemplo si hay solicitudes
        if created_requests > 0:
            sample_responses = [
                {
                    'request_id': 1,
                    'responder_name': 'Dra. Patricia Morales',
                    'responder_role': 'counselor',
                    'response_text': 'Hola Andrea, gracias por contactarnos. Lo que describes es completamente normal y más común de lo que piensas. El síndrome del impostor es muy frecuente en estudiantes de STEM, especialmente mujeres. Me gustaría programar una cita contigo para hablar más sobre estrategias que pueden ayudarte.',
                    'response_type': 'initial_contact'
                }
            ]
            
            created_responses = 0
            for resp_data in sample_responses:
                # Verificar que existe la solicitud
                request_exists = SupportRequest.query.get(resp_data['request_id'])
                if request_exists:
                    existing_response = SupportResponse.query.filter_by(
                        request_id=resp_data['request_id']
                    ).first()
                    
                    if not existing_response:
                        response = SupportResponse(
                            request_id=resp_data['request_id'],
                            responder_name=resp_data['responder_name'],
                            responder_role=resp_data['responder_role'],
                            response_text=resp_data['response_text'],
                            response_type=resp_data['response_type'],
                            created_at=datetime.utcnow() - timedelta(
                                days=random.randint(0, 3),
                                hours=random.randint(1, 12)
                            )
                        )
                        db.session.add(response)
                        created_responses += 1
            
            db.session.commit()
        else:
            created_responses = 0
        
        print("✅ Datos de ejemplo del sistema de apoyo creados")
        
        return {
            'created_requests': created_requests,
            'created_responses': created_responses,
            'total_requests': SupportRequest.query.count(),
            'total_responses': SupportResponse.query.count()
        }
        
    except Exception as e:
        print(f"Error creando datos de apoyo: {e}")
        return {
            'created_requests': 0,
            'created_responses': 0,
            'total_requests': 0,
            'total_responses': 0,
            'error': str(e)
        }