from flask import jsonify

def success_response(data=None, message=None, status_code=200):
    """
    Crée une réponse de succès standardisée.

    Args:
        data (any, optional): Les données à inclure dans la réponse. Par défaut None.
        message (str, optional): Un message de succès. Par défaut None.
        status_code (int, optional): Le code de statut HTTP. Par défaut 200.

    Returns:
        tuple: Un tuple contenant le JSON de réponse et le code de statut.
    """
    response = {"success": True}
    if data is not None:
        response["data"] = data
    if message is not None:
        response["message"] = message
    return jsonify(response), status_code

def error_response(message, status_code=400):
    """
    Crée une réponse d'erreur standardisée.

    Args:
        message (str): Le message d'erreur.
        status_code (int, optional): Le code de statut HTTP. Par défaut 400.

    Returns:
        tuple: Un tuple contenant le JSON de réponse et le code de statut.
    """
    return jsonify({"success": False, "error": message}), status_code

def validation_error_response(errors):
    """
    Crée une réponse d'erreur de validation standardisée.

    Args:
        errors (dict): Un dictionnaire d'erreurs de validation.

    Returns:
        tuple: Un tuple contenant le JSON de réponse et le code de statut.
    """
    return jsonify({"success": False, "errors": errors}), 422

def not_found_response(message="Resource not found"):
    """
    Crée une réponse standardisée pour les ressources non trouvées.

    Args:
        message (str, optional): Le message d'erreur. Par défaut "Resource not found".

    Returns:
        tuple: Un tuple contenant le JSON de réponse et le code de statut.
    """
    return jsonify({"success": False, "error": message}), 404

def unauthorized_response(message="Unauthorized"):
    """
    Crée une réponse standardisée pour les accès non autorisés.

    Args:
        message (str, optional): Le message d'erreur. Par défaut "Unauthorized".

    Returns:
        tuple: Un tuple contenant le JSON de réponse et le code de statut.
    """
    return jsonify({"success": False, "error": message}), 401

def forbidden_response(message="Forbidden"):
    """
    Crée une réponse standardisée pour les accès interdits.

    Args:
        message (str, optional): Le message d'erreur. Par défaut "Forbidden".

    Returns:
        tuple: Un tuple contenant le JSON de réponse et le code de statut.
    """
    return jsonify({"success": False, "error": message}), 403

def server_error_response(message="Internal server error"):
    """
    Crée une réponse standardisée pour les erreurs serveur.

    Args:
        message (str, optional): Le message d'erreur. Par défaut "Internal server error".

    Returns:
        tuple: Un tuple contenant le JSON de réponse et le code de statut.
    """
    return jsonify({"success": False, "error": message}), 500
