from flask import Blueprint, request, jsonify
from ..services import register_user, authenticate_user
from ..utils import success_response, error_response, validation_error_response

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/register", methods=["POST"])
def register():
    """
    Register a new user.
    
    Request body:
        wallet (str): The wallet address.
        password (str): The password.
        
    Returns:
        JSON: A success response with a message.
    """
    data = request.get_json()
    
    # Validate input
    wallet = data.get("wallet")
    password = data.get("password")
    
    if not wallet or not isinstance(wallet, str):
        return error_response("Adresse invalide", 400)
    
    if not password or not isinstance(password, str):
        return error_response("Mot de passe invalide", 400)
    
    try:
        # Register user
        register_user(wallet, password)
        return success_response(message="Inscription réussie")
    except ValueError as e:
        return error_response(str(e), 400)
    except Exception as e:
        return error_response("Erreur serveur", 500)

@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Authenticate a user.
    
    Request body:
        wallet (str): The wallet address.
        password (str): The password.
        
    Returns:
        JSON: A success response with an access token.
    """
    data = request.get_json()
    
    # Validate input
    wallet = data.get("wallet")
    password = data.get("password")
    
    if not wallet or not isinstance(wallet, str):
        return error_response("Adresse invalide", 400)
    
    if not password or not isinstance(password, str):
        return error_response("Mot de passe invalide", 400)
    
    try:
        # Authenticate user
        auth_data = authenticate_user(wallet, password)
        return success_response(data=auth_data)
    except ValueError as e:
        return error_response("Identifiants invalides", 401)
    except Exception as e:
        return error_response("Erreur serveur", 500)