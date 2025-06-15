import os

class Config:
    """Configuración base de la aplicación"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production'
    
    # Base de datos - usar PostgreSQL en producción si está disponible
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        # Render PostgreSQL URLs start with postgres:// but SQLAlchemy needs postgresql://
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        SQLALCHEMY_DATABASE_URI = database_url
    else:
        SQLALCHEMY_DATABASE_URI = 'sqlite:///stem_retention.db'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuración API Perplexity
    PERPLEXITY_API_KEY = os.environ.get('PERPLEXITY_API_KEY') or "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"
    PERPLEXITY_URL = "https://api.perplexity.ai/chat/completions"
    
    # Configuración del sistema de apoyo
    SUPPORT_CONFIG = {
        'MAX_MESSAGE_LENGTH': 1000,
        'CRISIS_THRESHOLD': 80,
        'HIGH_PRIORITY_THRESHOLD': 60,
        'EMERGENCY_KEYWORDS': [
            'suicidio', 'matarme', 'no puedo más', 'quiero morir', 
            'acabar con todo', 'lastimar', 'dolor insoportable',
            'crisis', 'emergencia', 'desesperada', 'sin salida'
        ]
    }
    
    # Configuración del predictor de riesgo
    RISK_CONFIG = {
        'MODEL_PATH': 'risk_model.pkl',
        'USE_RULE_BASED': True,
        'WEIGHTS': {
            'academic_performance': 0.2,
            'attendance': 0.15,
            'behavioral_factors': 0.65
        }
    }
    
    # Configuración de ROI
    ROI_CONFIG = {
        'cost_per_intervention': 150,  # USD
        'revenue_per_retained_student': 12000,  # Colegiatura anual
        'projected_retention_improvement': 0.25  # 25%
    }