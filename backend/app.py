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
from flask import Flask, redirect, url_for
from flask_cors import CORS
import logging
from .api import register_blueprints
from .models.base import Base, engine
from .config import Config

# --- Setup logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Log to console
        logging.FileHandler('backend.log')  # Also log to file
    ]
)
# Set debug level for specific modules to get more detailed logs
logging.getLogger('backend.modules.attack_generator').setLevel(logging.DEBUG)
logging.getLogger('backend.api.contract').setLevel(logging.DEBUG)

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

    # Health Check
    @app.route("/", methods=["GET"])
    def health_check():
        return "OK", 200

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

@app.route("/")
def home():
    # Génère l’URL de la vue 'login' du blueprint 'auth'
    return redirect(url_for("auth.login"))

# --- Run app ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
