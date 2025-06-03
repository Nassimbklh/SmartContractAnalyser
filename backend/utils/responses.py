from flask import jsonify

def success_response(data=None, message=None, status_code=200):
    """
    Create a standardized success response.
    
    Args:
        data (any, optional): The data to include in the response. Defaults to None.
        message (str, optional): A success message. Defaults to None.
        status_code (int, optional): The HTTP status code. Defaults to 200.
        
    Returns:
        tuple: A tuple containing the response JSON and the status code.
    """
    response = {"success": True}
    if data is not None:
        response["data"] = data
    if message is not None:
        response["message"] = message
    return jsonify(response), status_code

def error_response(message, status_code=400):
    """
    Create a standardized error response.
    
    Args:
        message (str): The error message.
        status_code (int, optional): The HTTP status code. Defaults to 400.
        
    Returns:
        tuple: A tuple containing the response JSON and the status code.
    """
    return jsonify({"success": False, "error": message}), status_code

def validation_error_response(errors):
    """
    Create a standardized validation error response.
    
    Args:
        errors (dict): A dictionary of validation errors.
        
    Returns:
        tuple: A tuple containing the response JSON and the status code.
    """
    return jsonify({"success": False, "errors": errors}), 422

def not_found_response(message="Resource not found"):
    """
    Create a standardized not found response.
    
    Args:
        message (str, optional): The error message. Defaults to "Resource not found".
        
    Returns:
        tuple: A tuple containing the response JSON and the status code.
    """
    return jsonify({"success": False, "error": message}), 404

def unauthorized_response(message="Unauthorized"):
    """
    Create a standardized unauthorized response.
    
    Args:
        message (str, optional): The error message. Defaults to "Unauthorized".
        
    Returns:
        tuple: A tuple containing the response JSON and the status code.
    """
    return jsonify({"success": False, "error": message}), 401

def forbidden_response(message="Forbidden"):
    """
    Create a standardized forbidden response.
    
    Args:
        message (str, optional): The error message. Defaults to "Forbidden".
        
    Returns:
        tuple: A tuple containing the response JSON and the status code.
    """
    return jsonify({"success": False, "error": message}), 403

def server_error_response(message="Internal server error"):
    """
    Create a standardized server error response.
    
    Args:
        message (str, optional): The error message. Defaults to "Internal server error".
        
    Returns:
        tuple: A tuple containing the response JSON and the status code.
    """
    return jsonify({"success": False, "error": message}), 500