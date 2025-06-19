from .contract_service import (
    analyze_contract, get_user_reports, get_report_by_filename,
    get_user_by_wallet as get_user_by_wallet_contract,
    save_report, generate_report_markdown
)
from .user_service import (
    register_user, authenticate_user,
    get_user_by_wallet as get_user_by_wallet_user
)
from .feedback_service import (
    save_feedback, get_feedback_by_user_and_report, get_report_by_id
)

# Resolve name conflict
def get_user_by_wallet(wallet):
    """
    Get a user by wallet address.

    Args:
        wallet (str): The wallet address.

    Returns:
        User: The user.
    """
    return get_user_by_wallet_user(wallet)

__all__ = [
    'analyze_contract', 'get_user_reports', 'get_report_by_filename',
    'save_report', 'generate_report_markdown',
    'register_user', 'authenticate_user', 'get_user_by_wallet',
    'save_feedback', 'get_feedback_by_user_and_report', 'get_report_by_id'
]
