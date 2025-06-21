from flask import Blueprint, request, jsonify
from ..services import (
    save_feedback, get_feedback_by_user_and_report, get_report_by_id,
    get_user_by_wallet
)
from ..utils import (
    token_required, success_response, error_response,
    not_found_response, server_error_response
)
import logging

logger = logging.getLogger(__name__)
feedback_bp = Blueprint('feedback', __name__)

@feedback_bp.route("/feedback", methods=["POST"])
@token_required
def submit_feedback(wallet):
    """
    Submit feedback for a report.
    
    Request body:
        report_id (int): The report ID.
        status (str): The feedback status ("OK" or "KO").
        comment (str, optional): The feedback comment.
        
    Returns:
        JSON: A success response.
    """
    logger.info(f"Received feedback submission from wallet: {wallet}")
    
    # Get request data
    data = request.json
    if not data:
        logger.warning("No data provided in feedback submission")
        return error_response("Aucune donnée fournie", 400)
    
    report_id = data.get("report_id")
    status = data.get("status")
    comment = data.get("comment")
    
    # Validate required fields
    if not report_id:
        logger.warning("No report_id provided in feedback submission")
        return error_response("ID du rapport manquant", 400)
    
    if not status:
        logger.warning("No status provided in feedback submission")
        return error_response("Statut manquant", 400)
    
    if status not in ["OK", "KO"]:
        logger.warning(f"Invalid status provided in feedback submission: {status}")
        return error_response("Statut invalide (doit être 'OK' ou 'KO')", 400)
    
    try:
        # Get user by wallet
        user = get_user_by_wallet(wallet)
        if not user:
            logger.warning(f"User not found for wallet: {wallet}")
            return not_found_response("Utilisateur non trouvé")
        
        # Check if report exists
        report = get_report_by_id(report_id)
        if not report:
            logger.warning(f"Report not found with ID: {report_id}")
            return not_found_response("Rapport introuvable")
        
        # Check if user has already submitted feedback for this report
        existing_feedback = get_feedback_by_user_and_report(user.id, report_id)
        if existing_feedback:
            logger.warning(f"User {user.id} has already submitted feedback for report {report_id}")
            return error_response("Vous avez déjà donné votre avis sur ce rapport", 400)
        
        # Save feedback
        feedback = save_feedback(user.id, report_id, status, comment)
        logger.info(f"Feedback saved with ID: {feedback.id}, status: {feedback.status}")
        
        return success_response(message="Merci pour votre retour !")
    except Exception as e:
        logger.error(f"Error during feedback submission: {str(e)}", exc_info=True)
        return server_error_response(str(e))