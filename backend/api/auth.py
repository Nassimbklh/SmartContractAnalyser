from flask import Blueprint, request, jsonify
from services import register_user, authenticate_user
from utils import success_response, error_response, validation_error_response
import logging

logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/register", methods=["POST"])
def register():
    """
    Register a new user.

    Request body:
        wallet (str): The wallet address.
        password (str): The password.
        technical_score (float, optional): The technical assessment score (0-5).
        technical_level (str, optional): The technical level based on the score.

    Returns:
        JSON: A success response with a message.
    """
    logger.info(f"Received register request with method: {request.method}")
    logger.info(f"Request headers: {dict(request.headers)}")
    logger.info(f"Request content type: {request.content_type}")

    # Handle both JSON and form data
    if request.is_json:
        logger.info("Processing JSON request")
        data = request.get_json()
    elif request.form:
        logger.info("Processing form data request")
        data = request.form
    else:
        logger.info("No data found in request")
        data = {}

    # Validate input
    wallet = data.get("wallet")
    password = data.get("password")
    technical_score = data.get("technical_score")
    technical_level = data.get("technical_level")

    if not wallet or not isinstance(wallet, str):
        return error_response("Adresse invalide", 400)

    if not password or not isinstance(password, str):
        return error_response("Mot de passe invalide", 400)

    # Validate technical_score if provided
    if technical_score is not None and not (isinstance(technical_score, (int, float)) and 0 <= technical_score <= 5):
        return error_response("Score technique invalide", 400)

    try:
        logger.info(f"Attempting to register user with wallet: {wallet}")
        # Register user
        register_user(wallet, password, technical_score, technical_level)
        logger.info(f"Registration successful for wallet: {wallet}")
        return success_response(message="Inscription réussie")
    except ValueError as e:
        logger.warning(f"Registration failed for wallet: {wallet}, error: {str(e)}")
        return error_response(str(e), 400)
    except Exception as e:
        logger.error(f"Server error during registration for wallet: {wallet}, error: {str(e)}", exc_info=True)
        return error_response("Erreur serveur", 500)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """
    Authenticate a user.

    Request body:
        wallet (str): The wallet address.
        password (str): The password.

    Returns:
        JSON: A success response with an access token.
    """
    logger.info(f"Received login request with method: {request.method}")
    logger.info(f"Request headers: {dict(request.headers)}")
    logger.info(f"Request content type: {request.content_type}")

    # Handle both JSON and form data
    if request.is_json:
        logger.info("Processing JSON request")
        data = request.get_json()
    elif request.form:
        logger.info("Processing form data request")
        data = request.form
    else:
        logger.info("No data found in request")
        data = {}

    # Validate input
    wallet = data.get("wallet")
    password = data.get("password")

    if not wallet or not isinstance(wallet, str):
        return error_response("Adresse invalide", 400)

    if not password or not isinstance(password, str):
        return error_response("Mot de passe invalide", 400)

    try:
        logger.info(f"Attempting to authenticate user with wallet: {wallet}")
        # Authenticate user
        auth_data = authenticate_user(wallet, password)
        logger.info(f"Authentication successful for wallet: {wallet}")
        return success_response(data=auth_data)
    except ValueError as e:
        logger.warning(f"Invalid credentials for wallet: {wallet}, error: {str(e)}")
        return error_response("Identifiants invalides", 401)
    except Exception as e:
        logger.error(f"Server error during authentication for wallet: {wallet}, error: {str(e)}", exc_info=True)
        return error_response("Erreur serveur", 500)
