import datetime
import os
import tempfile
from web3 import Web3
from ..models import Report, User
from ..config import Config
from ..modules import (
    compile_and_deploy_all_contracts,
    deploy_contract,
    setup_contract,
    auto_fund_contract_for_attack,
    build_multi_contract_observation,
    generate_complete_attack_strategy
)

def analyze_contract_from_code(content):
    """
    Analyze a smart contract from code string.

    Args:
        content (str): The smart contract code.

    Returns:
        dict: The analysis results.
    """
    # Create a temporary file for the contract code
    with tempfile.NamedTemporaryFile(suffix='.sol', delete=False, mode='w') as temp_file:
        temp_file.write(content)
        temp_path = temp_file.name

    try:
        # Set up Web3 connection to Ganache
        ganache_url = Config.GANACHE_URL
        w3 = Web3(Web3.HTTPProvider(ganache_url))

        # Compile the contract
        compiled_contracts = compile_and_deploy_all_contracts(temp_path)

        if not compiled_contracts:
            return {
                "status": "ERROR",
                "attack": "Compilation Error",
                "reasoning": "Failed to compile the contract. Please check the Solidity code for errors.",
                "summary": "Compilation error",
                "code": "",
                "contract_info": {
                    "contract_name": "Unknown",
                    "solc_version": "Unknown",
                    "address": "Unknown"
                }
            }

        # Deploy the contracts
        deployed_contracts = []
        for contract_info in compiled_contracts:
            deployed_contract = deploy_contract(contract_info, w3)
            if deployed_contract:
                # Setup the contract (call initialization functions)
                setup_contract(deployed_contract, w3)
                # Fund the contract for attack testing
                auto_fund_contract_for_attack(w3, deployed_contract)
                deployed_contracts.append(deployed_contract)

        if not deployed_contracts:
            return {
                "status": "ERROR",
                "attack": "Deployment Error",
                "reasoning": "Failed to deploy the contract. Please check the Solidity code for errors.",
                "summary": "Deployment error",
                "code": "",
                "contract_info": {
                    "contract_name": "Unknown",
                    "solc_version": "Unknown",
                    "address": "Unknown"
                }
            }

        # Build observation for analysis
        observation = build_multi_contract_observation(deployed_contracts, w3)

        # Generate attack strategy
        attack_strategy = generate_complete_attack_strategy(observation)

        # Determine if a vulnerability was found
        has_vulnerability = (
            attack_strategy.get("code", "") != "" and 
            "no vulnerabilit" not in attack_strategy.get("summary", "").lower()
        )

        # Prepare result
        result = {
            "status": "KO" if has_vulnerability else "OK",
            "attack": "Smart Contract Vulnerability" if has_vulnerability else None,
            "reasoning": attack_strategy.get("reasoning", ""),
            "summary": attack_strategy.get("summary", ""),
            "code": attack_strategy.get("code", ""),
            "contract_info": {
                "contract_name": deployed_contracts[0]["contract_name"],
                "solc_version": deployed_contracts[0]["solc_version"],
                "address": deployed_contracts[0]["address"]
            }
        }

        return result

    except Exception as e:
        return {
            "status": "ERROR",
            "attack": "Analysis Error",
            "reasoning": f"An error occurred during analysis: {str(e)}",
            "summary": "Analysis error",
            "code": "",
            "contract_info": {
                "contract_name": "Unknown",
                "solc_version": "Unknown",
                "address": "Unknown"
            }
        }
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_path):
            os.unlink(temp_path)

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

    # Set code_result based on status
    code_result = 1 if status == "OK" else 0

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
        code_result=code_result,
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
