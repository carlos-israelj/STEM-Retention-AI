import os
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from config import Config
from models import db

def create_app():
    """Factory function para crear la aplicación Flask"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Configuración específica para producción
    if os.environ.get('FLASK_ENV') == 'production':
        app.config['DEBUG'] = False
        app.config['TESTING'] = False
    
    # Inicializar base de datos
    db.init_app(app)
    
    # Registrar blueprints
    from routes.main_routes import main_bp
    from routes.student_routes import student_bp
    from routes.support_routes import support_bp
    from routes.admin_routes import admin_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(student_bp, url_prefix='/api/students')
    app.register_blueprint(support_bp, url_prefix='/api/support')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return render_template('home.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        return {'error': 'Internal server error'}, 500
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return {
            'status': 'healthy',
            'timestamp': db.func.now(),
            'version': '1.0.0'
        }, 200
    
    return app

def initialize_services():
    """Inicializar servicios globales"""
    try:
        from services.risk_predictor import RiskPredictor
        from services.data_simulator import DataSimulator
        
        global risk_predictor, data_simulator
        risk_predictor = RiskPredictor()
        data_simulator = DataSimulator()
        print("✅ Servicios inicializados correctamente")
        return True
    except Exception as e:
        print(f"⚠️ Error inicializando servicios: {e}")
        return False

# Crear la aplicación
app = create_app()

if __name__ == '__main__':
    with app.app_context():
        # Crear todas las tablas
        db.create_all()
        print("✅ Base de datos inicializada")
        
        # Inicializar servicios
        services_ok = initialize_services()
        
        if services_ok:
            print("🚀 STEM Retention AI iniciado correctamente")
            print("📋 URLs disponibles:")
            print("   🏠 Página de Inicio: /")
            print("   📊 Dashboard Administrativo: /dashboard")
            print("   🌟 Centro de Apoyo: /student_support.html")
            print("   👤 Vista de Estudiante: /student/<id>")
            print("")
            print("📋 APIs principales:")
            print("   🔄 Simular Datos: /api/admin/simulate_all_data")
            print("   👥 Estudiantes: /api/students/")
            print("   🤝 Mentoras: /api/admin/mentors")
            print("   📈 Estadísticas: /api/dashboard_stats")
            print("   💬 Sistema de Apoyo: /api/support/stats")
        else:
            print("⚠️ Sistema iniciado con errores en servicios")
    
    # Configuración para desarrollo vs producción
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    
    app.run(host='0.0.0.0', port=port, debug=debug)