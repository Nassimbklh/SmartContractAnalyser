import datetime
from ..models import Report, User
from ..rlhf_agent.agent import analyze_contract_from_code

def analyze_contract(content, user_id):
    """
    Analyze a smart contract and store the results in the database.
    
    Args:
        content (str): The smart contract code.
        user_id (int): The ID of the user who submitted the contract.
        
    Returns:
        dict: The analysis results.
    """
    # Analyze the contract
    analysis_result = analyze_contract_from_code(content)
    
    # Extract information from the analysis result
    status = analysis_result.get("status", "OK")
    attack = analysis_result.get("attack")
    contract_info = analysis_result.get("contract_info", {})
    now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
    contract_name = contract_info.get("contract_name", "Contract")
    generated_filename = f"{contract_name}_{now}"
    reasoning = analysis_result.get("reasoning", "")
    summary = analysis_result.get("summary", "")
    exploit_code = analysis_result.get("code", "")
    solc_version = contract_info.get("solc_version", "—")
    contract_address = contract_info.get("address", "—")
    
    # Create a new report
    report = Report(
        user_id=user_id,
        filename=generated_filename,
        status=status,
        attack=attack,
        contract_name=contract_name,
        contract_address=contract_address,
        solc_version=solc_version,
        summary=summary,
        reasoning=reasoning,
        exploit_code=exploit_code,
        created_at=datetime.datetime.now()
    )
    
    return {
        "report": report,
        "filename": generated_filename
    }

def get_user_reports(user_id):
    """
    Get all reports for a user.
    
    Args:
        user_id (int): The ID of the user.
        
    Returns:
        list: A list of reports.
    """
    from ..models.base import SessionLocal
    
    db = SessionLocal()
    try:
        reports = db.query(Report).filter_by(user_id=user_id).order_by(Report.created_at.desc()).all()
        return reports
    finally:
        db.close()

def get_report_by_filename(user_id, filename):
    """
    Get a report by filename.
    
    Args:
        user_id (int): The ID of the user.
        filename (str): The filename of the report.
        
    Returns:
        Report: The report.
    """
    from ..models.base import SessionLocal
    
    db = SessionLocal()
    try:
        report = db.query(Report).filter_by(user_id=user_id, filename=filename).first()
        return report
    finally:
        db.close()

def get_user_by_wallet(wallet):
    """
    Get a user by wallet address.
    
    Args:
        wallet (str): The wallet address.
        
    Returns:
        User: The user.
    """
    from ..models.base import SessionLocal
    
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(wallet=wallet).first()
        return user
    finally:
        db.close()

def save_report(report):
    """
    Save a report to the database.
    
    Args:
        report (Report): The report to save.
        
    Returns:
        Report: The saved report.
    """
    from ..models.base import SessionLocal
    
    db = SessionLocal()
    try:
        db.add(report)
        db.commit()
        db.refresh(report)
        return report
    finally:
        db.close()

def generate_report_markdown(report):
    """
    Generate a markdown report from a Report object.
    
    Args:
        report (Report): The report.
        
    Returns:
        str: The markdown report.
    """
    markdown_block = "```"
    exploit_section = f"""
## ⚔️ Code d'exploit proposé

{markdown_block}{report.exploit_code}
{markdown_block}
""" if report.exploit_code else "## ⚔️ Code d'exploit proposé\n\nAucun exploit exécutable généré."

    return f"""# 📄 Rapport d'analyse de contrat intelligent

**Nom du fichier :** {report.filename}  
**Nom du contrat :** {report.contract_name}  
**Adresse déployée :** {report.contract_address}  
**Compilateur Solidity :** {report.solc_version}  
**Date d'analyse :** {report.created_at.strftime('%Y-%m-%d %H:%M')}  

---

## ✅ Résultat global

**Statut :** {'❌ KO – Vulnérabilité détectée' if report.status == 'KO' else '✅ OK – Aucun comportement anormal détecté'}  
**Type de vulnérabilité :** {report.attack or 'Aucune'}

---

## 🔍 Résumé de l'analyse

{report.summary or 'Aucune vulnérabilité évidente détectée.'}

---

## 🧠 Raisonnement du modèle

{report.reasoning or 'Aucun raisonnement généré.'}

---

{exploit_section}

---

⚠️ **Note :** Ce rapport est généré automatiquement. Une validation humaine est conseillée.
"""