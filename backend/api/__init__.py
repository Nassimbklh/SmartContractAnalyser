from .auth import auth_bp
from .contract import contract_bp
from .feedback import feedback_bp

def register_blueprints(app):
    """
    Enregistre tous les blueprints avec l'application Flask.

    Args:
        app (Flask): L'application Flask.
    """
    app.register_blueprint(auth_bp)
    app.register_blueprint(contract_bp)
    app.register_blueprint(feedback_bp)

__all__ = ['register_blueprints', 'auth_bp', 'contract_bp', 'feedback_bp']
