import datetime
import os
import tempfile
import traceback
import logging
from web3 import Web3
from models import Report, User
from config import Config
from modules import (
    compile_and_deploy_all_contracts,
    deploy_contract,
    setup_contract,
    auto_fund_contract_for_attack,
    build_multi_contract_observation,
    generate_complete_attack_strategy,
    slither_analyze,
    execute_attack_on_contracts
)

logger = logging.getLogger(__name__)

def print_separator(title: str, char: str = "=", width: int = 80):
    """
    Affiche un séparateur de section avec un titre centré.
    """
    print(f"\n{char * width}")
    print(f"{title.center(width)}")
    print(f"{char * width}")

def try_single_attack(slith_result, observation, contract_group, w3):
    """
    Version simplifiée de try_attack_n_times qui ne fait qu'une seule tentative
    """
    print_separator("🧠 Génération de la stratégie d'attaque")

    # Générer la stratégie d'attaque
    attack_strategy = generate_complete_attack_strategy(slith_result, observation)
    code = attack_strategy.get('code')
    code_type = attack_strategy.get('code_type')

    if not code:
        print("❌ Aucun code d'attaque généré")
        return attack_strategy, None

    try:
        # Exécuter l'attaque
        attack_result = execute_attack_on_contracts(
            code,
            contract_group,
            w3,
            code_type=code_type
        )
    except Exception as e:
        print(f"❌ Erreur lors de l'exécution de l'attaque: {e}")
        return attack_strategy, None

    if attack_result.get('success'):
        print("✅ Attaque réussie!")
    else:
        print("❌ Attaque échouée")

    return attack_strategy, attack_result

def analyze_contract_from_code(content):
    """
    Analyze a smart contract from code string.

    Args:
        content (str): The smart contract code.

    Returns:
        dict: The analysis results.
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
                if not slith_result:
                    raise Exception("Slither analysis returned empty result")
                logger.info("Slither analysis completed successfully")
            except Exception as e:
                logger.error(f"Failed to run Slither analysis: {str(e)}")
                logger.error(traceback.format_exc())
                # Don't continue with empty Slither results if analysis fails
                return {
                    "status": "ERROR",
                    "attack": "Analysis Error",
                    "reasoning": f"Slither analysis failed: {str(e)}",
                    "summary": "Slither analysis error",
                    "code": "",
                    "contract_info": {
                        "contract_name": deployed_contracts[0]["contract_name"] if deployed_contracts else "Unknown",
                        "solc_version": deployed_contracts[0]["solc_version"] if deployed_contracts else "Unknown",
                        "address": deployed_contracts[0]["address"] if deployed_contracts else "Unknown"
                    }
                }

            # Generate and execute attack strategy with Slither results and observation
            try:
                attack_strategy, attack_result = try_single_attack(slith_result, observation, deployed_contracts, w3)

                if attack_result and attack_result.get('success'):
                    logger.info("Attaque exécutée avec succès")
                    # Ajouter des informations sur l'exécution de l'attaque au résultat
                    attack_strategy['execution_result'] = attack_result
                else:
                    logger.info("L'attaque n'a pas réussi ou n'a pas pu être exécutée")

                logger.info(f"Attack strategy generated successfully: {attack_strategy}")

                # Log detailed information about the attack strategy
                logger.debug(f"Attack strategy details:")
                logger.debug(f"  Summary: {attack_strategy.get('summary', 'None')}")
                logger.debug(f"  Reasoning: {attack_strategy.get('reasoning', 'None')}")
                logger.debug(f"  Code: {attack_strategy.get('code', 'None')}")
            except Exception as e:
                logger.error(f"Failed to generate attack strategy: {str(e)}")
                logger.error(traceback.format_exc())

                # Check for specific Runpod/LLM backend errors
                error_message = str(e)
                if "Runpod backend not reachable" in error_message:
                    return {
                        "status": "ERROR",
                        "attack": "Service Unavailable",
                        "reasoning": "Analyse non terminée — Runpod indisponible",
                        "summary": "Runpod backend not reachable",
                        "code": "",
                        "contract_info": {
                            "contract_name": deployed_contracts[0]["contract_name"],
                            "solc_version": deployed_contracts[0]["solc_version"],
                            "address": deployed_contracts[0]["address"]
                        }
                    }
                elif "LLM backend unreachable" in error_message or "502" in error_message:
                    return {
                        "status": "ERROR",
                        "attack": "Service Unavailable",
                        "reasoning": "Erreur critique — LLM backend unreachable",
                        "summary": "LLM backend unreachable",
                        "code": "",
                        "contract_info": {
                            "contract_name": deployed_contracts[0]["contract_name"],
                            "solc_version": deployed_contracts[0]["solc_version"],
                            "address": deployed_contracts[0]["address"]
                        }
                    }
                else:
                    return {
                        "status": "ERROR",
                        "attack": "Analysis Error",
                        "reasoning": f"Failed to generate attack strategy: {str(e)}",
                        "summary": "Analysis error",
                        "code": "",
                        "contract_info": {
                            "contract_name": deployed_contracts[0]["contract_name"],
                            "solc_version": deployed_contracts[0]["solc_version"],
                            "address": deployed_contracts[0]["address"]
                        }
                    }
        except Exception as e:
            logger.error(f"Unexpected error during attack strategy generation: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                "status": "ERROR",
                "attack": "Analysis Error",
                "reasoning": f"Failed to generate attack strategy: {str(e)}",
                "summary": "Analysis error",
                "code": "",
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
                "contract_info": {
                    "contract_name": deployed_contracts[0]["contract_name"],
                    "solc_version": deployed_contracts[0]["solc_version"],
                    "address": deployed_contracts[0]["address"]
                }
            }

        # Determine if a vulnerability was found
        has_code = attack_strategy.get("code", "") != ""
        no_vulnerabilities_mentioned = "no vulnerabilit" in attack_strategy.get("summary", "").lower()
        attack_executed = 'execution_result' in attack_strategy
        attack_succeeded = attack_executed and attack_strategy['execution_result'].get('success', False)

        logger.info(f"Has exploit code: {has_code}")
        logger.info(f"No vulnerabilities mentioned: {no_vulnerabilities_mentioned}")
        logger.info(f"Attack executed: {attack_executed}")
        logger.info(f"Attack succeeded: {attack_succeeded}")

        # A vulnerability is found if:
        # - there is exploit code AND the attack succeeded (if it was executed)
        # - OR if the summary mentions vulnerabilities (and doesn't explicitly say "no vulnerabilities")
        has_vulnerability = (has_code and (not attack_executed or attack_succeeded)) or not no_vulnerabilities_mentioned

        # If the summary explicitly says no vulnerabilities, force status to OK regardless of code
        if no_vulnerabilities_mentioned:
            logger.info("Summary explicitly states no vulnerabilities, setting status to OK")
            has_vulnerability = False

        logger.info(f"Final vulnerability determination: {has_vulnerability}")
        logger.info(f"Attack strategy summary: {attack_strategy.get('summary', '')}")

        # Prepare result
        result = {
            "status": "KO" if has_vulnerability else "OK",
            "attack": "Smart Contract Vulnerability" if has_vulnerability else None,
            "reasoning": attack_strategy.get("reasoning", ""),
            "summary": attack_strategy.get("summary", ""),
            "code": attack_strategy.get("code", ""),
            "contract_funding_success": True,  # Ajouter cette ligne pour indiquer si le contrat a été financé
            "attack_executed": attack_executed,  # Ajouter cette ligne pour indiquer si l'attaque a été exécutée
            "attack_succeeded": attack_succeeded,  # Ajouter cette ligne pour indiquer si l'attaque a réussi
            "contract_info": {
                "contract_name": deployed_contracts[0]["contract_name"],
                "solc_version": deployed_contracts[0]["solc_version"],
                "address": deployed_contracts[0]["address"]
            }
        }

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
    Analyze a smart contract and store the results in the database.

    Args:
        content (str): The smart contract code.
        user_id (int): The ID of the user who submitted the contract.

    Returns:
        dict: The analysis results.
    """
    # Analyze the contract
    analysis_result = analyze_contract_from_code(content)

    # Check if the code contains a valid contract
    is_contract = analysis_result.get("is_contract", True)

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

    # Extract the new fields from the analysis result
    contract_funding_success = analysis_result.get("contract_funding_success", False)
    attack_executed = analysis_result.get("attack_executed", False)
    attack_succeeded = analysis_result.get("attack_succeeded", False)

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
        contract_funding_success=contract_funding_success,
        attack_executed=attack_executed,
        attack_succeeded=attack_succeeded,
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

    # Ajouter ces lignes pour afficher les statuts de financement et d'attaque
    funding_status = "✅ Oui" if report.contract_funding_success else "❌ Non"
    attack_executed_status = "✅ Oui" if report.attack_executed else "❌ Non"
    attack_succeeded_status = "✅ Oui" if report.attack_succeeded else "❌ Non"

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

## 📊 Tableau détaillé final

| Indicateur | Statut |
|------------|--------|
| Contrat financé | {funding_status} |
| Attaque exécutée | {attack_executed_status} |
| Attaque réussie | {attack_succeeded_status} |

---

⚠️ **Note :** Ce rapport est généré automatiquement. Une validation humaine est conseillée.
"""
