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
    Soumettre un retour pour un rapport.

    Corps de la requête:
        report_id (int): L'ID du rapport.
        status (str): Le statut du retour ("OK" ou "KO").
        comment (str, optional): Le commentaire du retour.

    Returns:
        JSON: Une réponse de succès.
    """
    logger.info(f"Réception d'un retour depuis le portefeuille: {wallet}")

    # Récupérer les données de la requête
    data = request.json
    if not data:
        logger.warning("Aucune donnée fournie dans la soumission du retour")
        return error_response("Aucune donnée fournie", 400)

    report_id = data.get("report_id")
    status = data.get("status")
    comment = data.get("comment")

    # Valider les champs requis
    if not report_id:
        logger.warning("Aucun report_id fourni dans la soumission du retour")
        return error_response("ID du rapport manquant", 400)

    if not status:
        logger.warning("Aucun statut fourni dans la soumission du retour")
        return error_response("Statut manquant", 400)

    if status not in ["OK", "KO"]:
        logger.warning(f"Statut invalide fourni dans la soumission du retour: {status}")
        return error_response("Statut invalide (doit être 'OK' ou 'KO')", 400)

    try:
        # Récupérer l'utilisateur par portefeuille
        user = get_user_by_wallet(wallet)
        if not user:
            logger.warning(f"Utilisateur non trouvé pour le portefeuille: {wallet}")
            return not_found_response("Utilisateur non trouvé")

        # Vérifier si le rapport existe
        report = get_report_by_id(report_id)
        if not report:
            logger.warning(f"Rapport non trouvé avec l'ID: {report_id}")
            return not_found_response("Rapport introuvable")

        # Vérifier si l'utilisateur a déjà soumis un retour pour ce rapport
        existing_feedback = get_feedback_by_user_and_report(user.id, report_id)
        if existing_feedback:
            logger.warning(f"L'utilisateur {user.id} a déjà soumis un retour pour le rapport {report_id}")
            return error_response("Vous avez déjà donné votre avis sur ce rapport", 400)

        # Sauvegarder le retour
        feedback = save_feedback(user.id, report_id, status, comment)
        logger.info(f"Retour sauvegardé avec ID: {feedback.id}, statut: {feedback.status}, poids de la requête: {feedback.weight_request}")

        return success_response(message="Merci pour votre retour !")
    except Exception as e:
        logger.error(f"Erreur lors de la soumission du retour: {str(e)}", exc_info=True)
        return server_error_response(str(e))
