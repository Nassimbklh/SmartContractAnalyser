from flask import Blueprint, request, jsonify
from ..services import (
    analyze_contract, get_user_reports, get_report_by_filename,
    get_user_by_wallet, save_report, generate_report_markdown
)
from ..utils import (
    token_required, success_response, error_response,
    not_found_response, server_error_response
)

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
    file = request.files.get("file")
    code = request.form.get("code")
    content = code or (file.read().decode("utf-8") if file else "")

    if not content:
        return error_response("Aucun code fourni", 400)

    try:
        # Get user by wallet
        user = get_user_by_wallet(wallet)
        if not user:
            return not_found_response("Utilisateur non trouvé")

        # Analyze contract
        result = analyze_contract(content, user.id)

        # Save report
        report = result["report"]
        save_report(report)

        # Generate markdown report
        markdown = generate_report_markdown(report)

        return markdown, 200, {'Content-Type': 'text/markdown; charset=utf-8'}
    except Exception as e:
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
        formatted_reports = [
            {
                "filename": r.filename,
                "date": r.created_at.strftime("%Y-%m-%d %H:%M"),
                "status": r.status,
                "attack": r.attack
            } for r in reports
        ]

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
