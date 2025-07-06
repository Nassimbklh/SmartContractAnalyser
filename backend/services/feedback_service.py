from models import Feedback, User, Report, SessionLocal

def save_feedback(user_id, report_id, status, comment=None):
    """
    Save feedback for a report.

    Args:
        user_id (int): The user ID.
        report_id (int): The report ID.
        status (str): The feedback status ("OK" or "KO").
        comment (str, optional): The feedback comment.

    Returns:
        Feedback: The saved feedback.
    """
    # Set code_result based on status
    code_result = 1 if status == "OK" else 0

    # Get user's technical_score
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        technical_score = user.technical_score if user and user.technical_score is not None else 1
    finally:
        db.close()

    # Calculate weight_request based on code_result and technical_score
    weight_request = technical_score if code_result == 1 else 0

    # Create a new feedback
    feedback = Feedback(
        user_id=user_id,
        report_id=report_id,
        status=status,
        comment=comment,
        code_result=code_result,
        weight_request=weight_request
    )

    # Save to database
    db = SessionLocal()
    try:
        db.add(feedback)
        db.commit()
        db.refresh(feedback)
        return feedback
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def get_feedback_by_user_and_report(user_id, report_id):
    """
    Get feedback by user ID and report ID.

    Args:
        user_id (int): The user ID.
        report_id (int): The report ID.

    Returns:
        Feedback: The feedback, or None if not found.
    """
    db = SessionLocal()
    try:
        feedback = db.query(Feedback).filter(
            Feedback.user_id == user_id,
            Feedback.report_id == report_id
        ).first()
        return feedback
    finally:
        db.close()

def get_report_by_id(report_id):
    """
    Get a report by ID.

    Args:
        report_id (int): The report ID.

    Returns:
        Report: The report, or None if not found.
    """
    db = SessionLocal()
    try:
        report = db.query(Report).filter(Report.id == report_id).first()
        return report
    finally:
        db.close()
