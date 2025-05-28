# 🩹 Patch Python 3.12 pour inspect.getargspec (utilisé par parsimonious)
import inspect
from inspect import signature, Parameter

if not hasattr(inspect, "getargspec"):
    def getargspec(func):
        sig = signature(func)
        args = [p.name for p in sig.parameters.values() if p.kind in (Parameter.POSITIONAL_ONLY, Parameter.POSITIONAL_OR_KEYWORD)]
        varargs = next((p.name for p in sig.parameters.values() if p.kind == Parameter.VAR_POSITIONAL), None)
        varkw = next((p.name for p in sig.parameters.values() if p.kind == Parameter.VAR_KEYWORD), None)
        return type('ArgSpec', (), {
            'args': args, 'varargs': varargs, 'keywords': varkw, 'defaults': None
        })()
    inspect.getargspec = getargspec

# --- Imports ---
from flask import Flask
from flask_cors import CORS
import logging
from .api import register_blueprints
from .models.base import Base, engine
from .config import Config

# --- Setup logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Create app ---
def create_app():
    """
    Create and configure the Flask app.

    Returns:
        Flask: The configured Flask app.
    """
    # Create app
    app = Flask(__name__)

    # Configure app
    app.config.update(Config.get_config())

    # Setup CORS
    CORS(app)

    # Create database tables
    Base.metadata.create_all(bind=engine)

    # Register blueprints
    register_blueprints(app)

    # Log startup
    logger.info("Application started")

    return app

# --- Create app instance ---
app = create_app()

# --- Run app ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
