from flask import Blueprint, request, jsonify
from ..services import (
    analyze_contract, get_user_reports, get_report_by_filename,
    get_user_by_wallet, save_report, generate_report_markdown
)
from ..utils import (
    token_required, success_response, error_response,
    not_found_response, server_error_response
)
import logging

logger = logging.getLogger(__name__)
contract_bp = Blueprint('contract', __name__)

@contract_bp.route("/analyze", methods=["POST"])
@token_required
def analyze(wallet):
    """
    Analyze a smart contract.

    Request body:
        file (file, optional): The smart contract file.
        code (str, optional): The smart contract code.

    Returns:
        str: The markdown report content.
    """
    logger.info(f"Received analyze request from wallet: {wallet}")

    file = request.files.get("file")
    code = request.form.get("code")

    if file:
        logger.info(f"Analyzing file: {file.filename}")
        content = file.read().decode("utf-8")
    elif code:
        logger.info("Analyzing code snippet")
        content = code
    else:
        content = ""

    if not content:
        logger.warning("No content provided for analysis")
        return error_response("Aucun code fourni", 400)

    try:
        # Get user by wallet
        user = get_user_by_wallet(wallet)
        if not user:
            logger.warning(f"User not found for wallet: {wallet}")
            return not_found_response("Utilisateur non trouvé")

        logger.info(f"Starting contract analysis for user: {user.id}")
        # Analyze contract
        result = analyze_contract(content, user.id)

        # Check if the code contains a valid contract
        if not result.get("is_contract", True):
            logger.warning("No valid Solidity contract found in the provided code")
            return jsonify({
                "status": "ERROR",
                "message": result.get("message", "❌ Le code fourni ne contient pas de contrat Solidity valide."),
                "is_contract": False
            }), 400

        # Save report
        report = result["report"]
        save_report(report)
        logger.info(f"Report saved with filename: {report.filename}, status: {report.status}")

        # Generate markdown report
        markdown = generate_report_markdown(report)
        logger.info("Analysis completed successfully, returning report")

        return markdown, 200, {'Content-Type': 'text/markdown; charset=utf-8'}
    except Exception as e:
        logger.error(f"Error during contract analysis: {str(e)}", exc_info=True)
        return server_error_response(str(e))

@contract_bp.route("/history", methods=["GET"])
@token_required
def history(wallet):
    """
    Get the history of analyzed contracts.

    Returns:
        JSON: A success response with a list of reports.
    """
    try:
        # Get user by wallet
        user = get_user_by_wallet(wallet)
        if not user:
            return not_found_response("Utilisateur non trouvé")

        # Get reports
        reports = get_user_reports(user.id)

        # Format reports
        formatted_reports = []
        for r in reports:
            # Check if user has provided feedback for this report
            user_feedback = None
            for feedback in r.feedbacks:
                if feedback.user_id == user.id:
                    user_feedback = feedback
                    break

            report_data = {
                "id": r.id,
                "filename": r.filename,
                "date": r.created_at.strftime("%Y-%m-%d %H:%M"),
                "status": r.status,
                "attack": r.attack,
                "feedback": None
            }

            # Include feedback if it exists
            if user_feedback:
                report_data["feedback"] = {
                    "status": user_feedback.status,
                    "code_result": user_feedback.code_result,
                    "comment": user_feedback.comment
                }

            formatted_reports.append(report_data)

        return success_response(data=formatted_reports)
    except Exception as e:
        return server_error_response(str(e))

@contract_bp.route("/report/<wallet>/<filename>", methods=["GET"])
@token_required
def download_report(token_wallet, wallet, filename):
    """
    Download a report.

    Path parameters:
        wallet (str): The wallet address.
        filename (str): The filename of the report.

    Returns:
        str: The report in markdown format.
    """
    if token_wallet != wallet:
        return error_response("Accès interdit", 403)

    try:
        # Get user by wallet
        user = get_user_by_wallet(wallet)
        if not user:
            return not_found_response("Utilisateur non trouvé")

        # Get report
        report = get_report_by_filename(user.id, filename)
        if not report:
            return not_found_response("Rapport introuvable")

        # Generate markdown
        markdown = generate_report_markdown(report)

        return markdown, 200, {'Content-Type': 'text/markdown; charset=utf-8'}
    except Exception as e:
        return server_error_response(str(e))
