from flask import Blueprint, request, jsonify
from utils import token_required, success_response, error_response, server_error_response
import requests
import logging
import os
from config.config import Config

logger = logging.getLogger(__name__)
soleval_bp = Blueprint('soleval', __name__)

# Configuration RunPod
POD_ID = os.getenv("RUNPOD_ID", "r3etcvinyjvth2")
SOLEVAL_URL = f"https://{POD_ID}-80.proxy.runpod.net/soleval"

@soleval_bp.route("/soleval", methods=["POST"])
@token_required
def run_soleval(wallet):
    """
    Lance une évaluation SolEval sur le modèle fine-tuné.
    
    Corps de la requête:
        evaluation_type (str, optional): Type d'évaluation ("full", "quick")
        include_reference (bool, optional): Inclure la comparaison avec le modèle de référence
    
    Returns:
        JSON: Résultats de l'évaluation SolEval
    """
    logger.info(f"Lancement de SolEval depuis le portefeuille: {wallet}")
    
    try:
        data = request.json or {}
        evaluation_type = data.get("evaluation_type", "full")
        include_reference = data.get("include_reference", True)
        
        # Préparer la requête pour RunPod
        payload = {
            "action": "evaluate",
            "model_type": "finetuned",
            "evaluation_type": evaluation_type,
            "include_reference": include_reference,
            "test_categories": [
                "vulnerability_detection",
                "code_understanding",
                "security_best_practices",
                "attack_vector_identification"
            ]
        }
        
        # Appeler RunPod
        logger.info(f"Envoi de la requête SolEval à RunPod: {SOLEVAL_URL}")
        response = requests.post(
            SOLEVAL_URL,
            json=payload,
            timeout=300  # 5 minutes de timeout pour l'évaluation
        )
        
        if response.status_code != 200:
            logger.error(f"Erreur RunPod: {response.status_code} - {response.text}")
            return error_response(
                f"Erreur lors de l'évaluation: {response.text}",
                response.status_code
            )
        
        results = response.json()
        
        # Enrichir les résultats avec des métadonnées
        results["evaluation_metadata"] = {
            "wallet": wallet,
            "evaluation_type": evaluation_type,
            "include_reference": include_reference
        }
        
        logger.info("Évaluation SolEval terminée avec succès")
        return success_response(
            data=results,
            message="Évaluation SolEval terminée avec succès"
        )
        
    except requests.Timeout:
        logger.error("Timeout lors de l'appel à RunPod")
        return error_response(
            "L'évaluation a pris trop de temps. Veuillez réessayer.",
            504
        )
    except requests.RequestException as e:
        logger.error(f"Erreur de requête vers RunPod: {str(e)}")
        return error_response(
            "Impossible de contacter le service d'évaluation",
            503
        )
    except Exception as e:
        logger.error(f"Erreur lors de l'évaluation SolEval: {str(e)}", exc_info=True)
        return server_error_response(str(e))


@soleval_bp.route("/soleval/status", methods=["GET"])
@token_required
def get_soleval_status(wallet):
    """
    Vérifie le statut du service SolEval.
    
    Returns:
        JSON: Statut du service
    """
    logger.info(f"Vérification du statut SolEval depuis le portefeuille: {wallet}")
    
    try:
        # Vérifier la disponibilité du service
        response = requests.get(
            f"{SOLEVAL_URL}/health",
            timeout=10
        )
        
        if response.status_code == 200:
            return success_response(
                data={
                    "status": "available",
                    "pod_id": POD_ID,
                    "service": "SolEval"
                },
                message="Service SolEval disponible"
            )
        else:
            return error_response(
                "Service SolEval indisponible",
                503
            )
            
    except Exception as e:
        logger.error(f"Erreur lors de la vérification du statut: {str(e)}")
        return error_response(
            "Impossible de vérifier le statut du service",
            503
        )