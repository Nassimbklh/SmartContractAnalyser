from .auth import auth_bp
from .contract import contract_bp

def register_blueprints(app):
    """
    Register all blueprints with the Flask app.
    
    Args:
        app (Flask): The Flask app.
    """
    app.register_blueprint(auth_bp)
    app.register_blueprint(contract_bp)

__all__ = ['register_blueprints', 'auth_bp', 'contract_bp']
