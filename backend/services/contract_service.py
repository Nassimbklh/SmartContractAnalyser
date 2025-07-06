import datetime
import os
import tempfile
import traceback
import logging
from web3 import Web3
from models import Report, User
from config import Config
from solcx import install_solc, set_solc_version

install_solc("0.8.20")
set_solc_version("0.8.20")
from modules import (
    compile_and_deploy_all_contracts,
    deploy_contract,
    setup_contract,
    auto_fund_contract_for_attack,
    build_multi_contract_observation,
    generate_complete_attack_strategy,
    slither_analyze
)

logger = logging.getLogger(__name__)

def analyze_contract_from_code(content):
    """
    Analyze a smart contract from code string.

    Args:
        content (str): The smart contract code.

    Returns:
        dict: The analysis results with the following structure:
            - status (str): The status of the analysis (OK, KO, ERROR)
            - attack (str or None): The type of attack or vulnerability found
            - reasoning (str): Detailed explanation of the analysis
            - summary (str): Brief summary of the analysis
            - code (str): Exploit code if a vulnerability was found
            - is_contract (bool): Whether the code contains a valid Solidity contract
            - contract_info (dict): Information about the contract (name, version, address)
    """
    # Create a temporary file for the contract code
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix='.sol', delete=False, mode='w') as temp_file:
            temp_file.write(content)
            temp_path = temp_file.name

        logger.info(f"Created temporary file for contract code: {temp_path}")

        # Set up Web3 connection to Ganache
        try:
            ganache_url = Config.GANACHE_URL
            w3 = Web3(Web3.HTTPProvider(ganache_url))
            logger.info(f"Connected to Ganache at {ganache_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Ganache: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                "status": "ERROR",
                "attack": "Connection Error",
                "reasoning": f"Failed to connect to Ganache: {str(e)}",
                "summary": "Connection error",
                "code": "",
                "is_contract": True,
                "contract_info": {
                    "contract_name": "Unknown",
                    "solc_version": "Unknown",
                    "address": "Unknown"
                }
            }

        # Compile the contract
        try:
            logger.info("Compiling contract...")
            compiled_contracts = compile_and_deploy_all_contracts(temp_path)
            logger.info(f"Compilation result: {len(compiled_contracts) if compiled_contracts else 0} contracts compiled")
        except Exception as e:
            logger.error(f"Failed to compile contract: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                "status": "ERROR",
                "attack": "Compilation Error",
                "reasoning": f"Failed to compile the contract: {str(e)}",
                "summary": "Compilation error",
                "code": "",
                "is_contract": True,
                "contract_info": {
                    "contract_name": "Unknown",
                    "solc_version": "Unknown",
                    "address": "Unknown"
                }
            }

        if not compiled_contracts:
            logger.warning("No contracts compiled")
            return {
                "status": "ERROR",
                "attack": "Compilation Error",
                "reasoning": "❌ Le code fourni ne contient pas de contrat Solidity valide.",
                "summary": "Compilation error",
                "code": "",
                "is_contract": False,
                "contract_info": {
                    "contract_name": "Unknown",
                    "solc_version": "Unknown",
                    "address": "Unknown"
                }
            }

        # Deploy the contracts
        deployed_contracts = []
        try:
            logger.info(f"Deploying {len(compiled_contracts)} contracts...")
            for contract_info in compiled_contracts:
                try:
                    deployed_contract = deploy_contract(contract_info, w3)
                    if deployed_contract:
                        logger.info(f"Contract {deployed_contract['contract_name']} deployed at {deployed_contract['address']}")

                        # Setup the contract (call initialization functions)
                        try:
                            logger.info(f"Setting up contract {deployed_contract['contract_name']}...")
                            setup_contract(deployed_contract, w3)
                            logger.info(f"Contract {deployed_contract['contract_name']} setup completed")
                        except Exception as e:
                            logger.warning(f"Failed to setup contract {deployed_contract['contract_name']}: {str(e)}")
                            logger.warning(traceback.format_exc())
                            # Continue with the analysis even if setup fails

                        # Fund the contract for attack testing
                        try:
                            logger.info(f"Funding contract {deployed_contract['contract_name']} for attack testing...")
                            auto_fund_contract_for_attack(w3, deployed_contract)
                            logger.info(f"Contract {deployed_contract['contract_name']} funded")
                        except Exception as e:
                            logger.warning(f"Failed to fund contract {deployed_contract['contract_name']}: {str(e)}")
                            logger.warning(traceback.format_exc())
                            # Continue with the analysis even if funding fails

                        deployed_contracts.append(deployed_contract)
                except Exception as e:
                    logger.warning(f"Failed to deploy contract: {str(e)}")
                    logger.warning(traceback.format_exc())
                    # Continue with other contracts
        except Exception as e:
            logger.error(f"Failed to deploy contracts: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                "status": "ERROR",
                "attack": "Deployment Error",
                "reasoning": f"Failed to deploy the contract: {str(e)}",
                "summary": "Deployment error",
                "code": "",
                "is_contract": True,
                "contract_info": {
                    "contract_name": "Unknown",
                    "solc_version": "Unknown",
                    "address": "Unknown"
                }
            }

        if not deployed_contracts:
            logger.warning("No contracts deployed")
            return {
                "status": "ERROR",
                "attack": "Deployment Error",
                "reasoning": "Failed to deploy the contract. Please check the Solidity code for errors.",
                "summary": "Deployment error",
                "code": "",
                "is_contract": True,
                "contract_info": {
                    "contract_name": "Unknown",
                    "solc_version": "Unknown",
                    "address": "Unknown"
                }
            }

        # Build observation for analysis
        try:
            logger.info("Building contract observation...")
            observation = build_multi_contract_observation(deployed_contracts, w3)
            logger.info("Contract observation built successfully")
        except Exception as e:
            logger.error(f"Failed to build contract observation: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                "status": "ERROR",
                "attack": "Analysis Error",
                "reasoning": f"Failed to build contract observation: {str(e)}",
                "summary": "Analysis error",
                "code": "",
                "is_contract": True,
                "contract_info": {
                    "contract_name": deployed_contracts[0]["contract_name"] if deployed_contracts else "Unknown",
                    "solc_version": deployed_contracts[0]["solc_version"] if deployed_contracts else "Unknown",
                    "address": deployed_contracts[0]["address"] if deployed_contracts else "Unknown"
                }
            }

        # Generate attack strategy
        try:
            logger.info("Generating attack strategy...")

            # Generate Slither analysis results
            logger.info("Running Slither analysis...")
            try:
                slith_result = slither_analyze(temp_path)
                logger.info("Slither analysis completed successfully")
            except Exception as e:
                logger.warning(f"Failed to run Slither analysis: {str(e)}")
                logger.warning(traceback.format_exc())
                # Continue with empty Slither results if analysis fails
                slith_result = ""

            # Generate attack strategy with Slither results and observation
            attack_strategy = generate_complete_attack_strategy(slith_result, observation)
            logger.info(f"Attack strategy generated successfully: {attack_strategy}")

            # Log detailed information about the attack strategy
            logger.debug(f"Attack strategy details:")
            logger.debug(f"  Summary: {attack_strategy.get('summary', 'None')}")
            logger.debug(f"  Reasoning: {attack_strategy.get('reasoning', 'None')}")
            logger.debug(f"  Code: {attack_strategy.get('code', 'None')}")
        except Exception as e:
            logger.error(f"Failed to generate attack strategy: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                "status": "ERROR",
                "attack": "Analysis Error",
                "reasoning": f"Failed to generate attack strategy: {str(e)}",
                "summary": "Analysis error",
                "code": "",
                "is_contract": True,
                "contract_info": {
                    "contract_name": deployed_contracts[0]["contract_name"],
                    "solc_version": deployed_contracts[0]["solc_version"],
                    "address": deployed_contracts[0]["address"]
                }
            }

        # Handle case where attack_strategy is None or empty
        if not attack_strategy:
            logger.warning("Attack strategy is None or empty, setting status to OK")
            return {
                "status": "OK",
                "attack": None,
                "reasoning": "No vulnerabilities detected in the contract.",
                "summary": "The contract appears to be secure.",
                "code": "",
                "is_contract": True,
                "contract_info": {
                    "contract_name": deployed_contracts[0]["contract_name"],
                    "solc_version": deployed_contracts[0]["solc_version"],
                    "address": deployed_contracts[0]["address"]
                }
            }

        # Determine if a vulnerability was found
        has_code = attack_strategy.get("code", "") != ""
        no_vulnerabilities_mentioned = "no vulnerabilit" in attack_strategy.get("summary", "").lower()

        logger.info(f"Has exploit code: {has_code}")
        logger.info(f"No vulnerabilities mentioned: {no_vulnerabilities_mentioned}")

        # A vulnerability is found if there is exploit code AND the summary doesn't say "no vulnerabilities"
        has_vulnerability = has_code and not no_vulnerabilities_mentioned

        # If the summary explicitly says no vulnerabilities, force status to OK regardless of code
        if no_vulnerabilities_mentioned:
            logger.info("Summary explicitly states no vulnerabilities, setting status to OK")
            has_vulnerability = False

        logger.info(f"Final vulnerability determination: {has_vulnerability}")
        logger.info(f"Attack strategy summary: {attack_strategy.get('summary', '')}")

        # Prepare result
        result = {"status": "KO" if has_vulnerability else "OK",
                  "attack": "Smart Contract Vulnerability" if has_vulnerability else None,
                  "reasoning": attack_strategy.get("reasoning", ""), "summary": attack_strategy.get("summary", ""),
                  "code": attack_strategy.get("code", ""), "contract_info": {
                "contract_name": deployed_contracts[0]["contract_name"],
                "solc_version": deployed_contracts[0]["solc_version"],
                "address": deployed_contracts[0]["address"]
            }, "is_contract": True}

        # ✅ Rajoute explicitement
        logger.info(f"Analysis completed with status: {result['status']}")
        return result

    except Exception as e:
        logger.error(f"Unexpected error during contract analysis: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "status": "ERROR",
            "attack": "Analysis Error",
            "reasoning": f"An error occurred during analysis: {str(e)}",
            "summary": "Analysis error",
            "code": "",
            "is_contract": True,
            "contract_info": {
                "contract_name": "Unknown",
                "solc_version": "Unknown",
                "address": "Unknown"
            }
        }
    finally:
        # Clean up the temporary file
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
                logger.info(f"Temporary file {temp_path} removed")
            except Exception as e:
                logger.warning(f"Failed to remove temporary file {temp_path}: {str(e)}")
                logger.warning(traceback.format_exc())

def analyze_contract(content, user_id):
    """
    Analyze a smart contract and prepare a Report object for database storage.

    This function calls analyze_contract_from_code to perform the actual analysis,
    then processes the results to create a Report object. Note that this function
    does NOT save the Report object to the database; it returns it for the caller
    to save using the save_report function.

    Args:
        content (str): The smart contract code.
        user_id (int): The ID of the user who submitted the contract.

    Returns:
        dict: The analysis results with the following structure:
            - is_contract (bool): Whether the code contains a valid Solidity contract
            - report (Report, optional): The Report object if is_contract is True
            - filename (str, optional): The generated filename if is_contract is True
            - message (str, optional): Error message if is_contract is False
    """
    # Analyze the contract
    analysis_result = analyze_contract_from_code(content)

    # Check if the code contains a valid contract
    is_contract = analysis_result["is_contract"]  # This key is now guaranteed to exist

    # If not a valid contract, return early with the error message
    if not is_contract:
        return {
            "is_contract": False,
            "message": analysis_result.get("reasoning", "❌ Le code fourni ne contient pas de contrat Solidity valide.")
        }

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
        "is_contract": True,
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
    from models.base import SessionLocal
    from sqlalchemy.orm import joinedload

    db = SessionLocal()
    try:
        reports = db.query(Report).options(joinedload(Report.feedbacks)).filter_by(user_id=user_id).order_by(Report.created_at.desc()).all()
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
    from models.base import SessionLocal

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
    from models.base import SessionLocal

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
    from models.base import SessionLocal

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
