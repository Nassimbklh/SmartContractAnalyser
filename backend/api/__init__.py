from .auth import auth_bp
from .contract import contract_bp
from .feedback import feedback_bp
from .finetune import finetune_bp
from .soleval import soleval_bp
from .evaluation_gpt import evaluation_gpt_bp

def register_blueprints(app):
    """
    Enregistre tous les blueprints avec l'application Flask.

    Args:
        app (Flask): L'application Flask.
    """
    app.register_blueprint(auth_bp)
    app.register_blueprint(contract_bp)
    app.register_blueprint(feedback_bp)
    app.register_blueprint(finetune_bp)
    app.register_blueprint(soleval_bp)
    app.register_blueprint(evaluation_gpt_bp)

__all__ = ['register_blueprints', 'auth_bp', 'contract_bp', 'feedback_bp', 'finetune_bp', 'soleval_bp', 'evaluation_gpt_bp']
