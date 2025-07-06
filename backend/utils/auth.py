import jwt
from functools import wraps
from flask import request, jsonify
from datetime import datetime, timedelta, UTC
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config

def token_required(f):
    """
    Decorator for routes that require a valid JWT token.

    Args:
        f (function): The function to decorate.

    Returns:
        function: The decorated function.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', "").replace("Bearer ", "")
        if not token:
            return jsonify({"error": "Token manquant"}), 401
        try:
            data = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
            return f(data["wallet"], *args, **kwargs)
        except:
            return jsonify({"error": "Token invalide"}), 401
    return decorated

def create_token(wallet):
    """
    Create a JWT token for the given wallet.

    Args:
        wallet (str): The wallet address.

    Returns:
        str: The JWT token.
    """
    return jwt.encode({
        "wallet": wallet,
        "exp": datetime.now(UTC) + Config.JWT_ACCESS_TOKEN_EXPIRES
    }, Config.SECRET_KEY, algorithm="HS256")

def hash_password(password):
    """
    Hash a password.

    Args:
        password (str): The password to hash.

    Returns:
        str: The hashed password.
    """
    return generate_password_hash(password)

def check_password(hashed_password, password):
    """
    Check if a password matches a hash.

    Args:
        hashed_password (str): The hashed password.
        password (str): The password to check.

    Returns:
        bool: True if the password matches the hash, False otherwise.
    """
    return check_password_hash(hashed_password, password)
