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
from api import register_blueprints
from models.base import Base, engine
from config import Config

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
logging.getLogger('backend.api.auth').setLevel(logging.DEBUG)
logging.getLogger('backend.services.contract_service').setLevel(logging.DEBUG)
logging.getLogger('flask_cors').setLevel(logging.DEBUG)

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

    # Add custom error handler for CORS errors
    @app.errorhandler(500)
    def handle_500(e):
        logger.error(f"Internal Server Error: {str(e)}")
        return {"error": "Internal Server Error", "message": str(e)}, 500

    # Setup CORS with explicit configuration
    CORS(app, resources={r"/*": {
        "origins": "*",  # Allow all origins for testing
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        "allow_headers": ["Content-Type", "Authorization", "X-Requested-With", "Accept", "Origin", "Access-Control-Request-Method", "Access-Control-Request-Headers"],
        "expose_headers": ["Content-Type", "Content-Length", "Content-Disposition", "Authorization"],
        "supports_credentials": False,  # Must be False when origins is "*"
        "max_age": 86400
    }})

    # Create database tables
    Base.metadata.create_all(bind=engine)

    # Register blueprints
    register_blueprints(app)

    # Add a test route for CORS
    @app.route('/cors-test', methods=['GET', 'OPTIONS'])
    def cors_test():
        logger.info("CORS test route accessed")
        return {"message": "CORS is working"}, 200

    # Log startup
    logger.info("Application started")

    return app

# --- Create app instance ---
app = create_app()

# --- Run app ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
