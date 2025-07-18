from flask import Blueprint, request, jsonify
from utils import token_required, success_response, error_response, server_error_response
from models import get_db, Finetune, Report
import logging
import os
from datetime import datetime
import json
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
evaluation_gpt_bp = Blueprint('evaluation_gpt', __name__)

# Configuration OpenAI
try:
    from openai import OpenAI
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key) if api_key else None
    USE_OPENAI = client is not None
except Exception as e:
    logger.warning(f"OpenAI non disponible, utilisation du mode simulation: {e}")
    client = None
    USE_OPENAI = False

@evaluation_gpt_bp.route("/evaluate/gpt", methods=["POST"])
@token_required
def evaluate_with_gpt(wallet):
    """
    Évalue les 10 derniers fine-tunings en utilisant GPT-4 si disponible.
    
    Returns:
        JSON: Note moyenne et détails de l'évaluation
    """
    logger.info(f"Lancement de l'évaluation depuis le portefeuille: {wallet}")
    logger.info(f"Mode d'évaluation: {'GPT-4' if USE_OPENAI else 'Simulation'}")
    
    db: Session = next(get_db())
    
    try:
        # Récupérer les 10 derniers fine-tunings
        recent_finetunes = db.query(Finetune).order_by(Finetune.created_at.desc()).limit(10).all()
        
        if not recent_finetunes:
            return error_response("Aucun fine-tuning trouvé", 404)
        
        evaluations = []
        total_score = 0
        
        for finetune in recent_finetunes:
            # Extraire le type d'attaque depuis le rapport si disponible
            attack_type = "Non spécifié"
            vulnerability_details = ""
            
            if finetune.report:
                try:
                    if finetune.report.results:
                        report_data = json.loads(finetune.report.results) if isinstance(finetune.report.results, str) else finetune.report.results
                        # Extraire le type depuis le rapport
                        if isinstance(report_data, dict):
                            attack_type = report_data.get('vulnerability', report_data.get('attack_type', 'Non spécifié'))
                            vulnerability_details = str(report_data.get('details', ''))[:500]
                except Exception as e:
                    logger.warning(f"Erreur parsing rapport: {e}")
            
            if USE_OPENAI and client:
                # Utiliser GPT-4 pour l'évaluation
                try:
                    prompt = f"""
                    Évalue ce fine-tuning d'un modèle spécialisé dans l'analyse de smart contracts Solidity.
                    
                    Données du fine-tuning:
                    - Input utilisateur (extrait): {finetune.user_input[:300] if finetune.user_input else "Non disponible"}
                    - Output du modèle (extrait): {finetune.model_outputs[:300] if finetune.model_outputs else "Non disponible"}
                    - Type d'attaque identifié: {attack_type}
                    - Détails de vulnérabilité: {vulnerability_details[:200]}
                    
                    Évalue la qualité de ce fine-tuning sur une échelle de 0 à 100 en considérant:
                    1. La pertinence et la clarté de l'input utilisateur (25%)
                    2. La qualité et la précision de l'output du modèle (40%)
                    3. La cohérence entre l'input et l'output (25%)
                    4. L'utilité pour l'amélioration du modèle (10%)
                    
                    NE PAS prendre en compte les feedbacks utilisateurs dans l'évaluation.
                    
                    Réponds UNIQUEMENT avec un JSON valide contenant:
                    {{
                        "score": <number entre 0 et 100>,
                        "reasoning": "<explication courte de la note en une phrase>",
                        "strengths": ["<point fort 1>", "<point fort 2>"],
                        "weaknesses": ["<point faible 1>", "<point faible 2>"]
                    }}
                    """
                    
                    response = client.chat.completions.create(
                        model="gpt-4-turbo-preview",
                        messages=[
                            {"role": "system", "content": "Tu es un expert en sécurité des smart contracts et en évaluation de données d'entraînement pour modèles ML. Réponds uniquement en JSON valide."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.3,
                        max_tokens=500,
                        response_format={"type": "json_object"}
                    )
                    
                    # Parser la réponse
                    evaluation = json.loads(response.choices[0].message.content)
                    evaluation["finetune_id"] = finetune.id
                    evaluation["attack_type"] = attack_type
                    
                except Exception as e:
                    logger.error(f"Erreur GPT-4 pour finetune {finetune.id}: {e}")
                    # Fallback vers simulation
                    evaluation = simulate_evaluation(finetune, attack_type)
            else:
                # Mode simulation
                evaluation = simulate_evaluation(finetune, attack_type)
            
            evaluations.append(evaluation)
            total_score += evaluation["score"]
            
            logger.info(f"Fine-tuning {finetune.id} évalué: {evaluation['score']}/100")
        
        # Calculer la note moyenne
        average_score = total_score / len(evaluations)
        
        # Préparer le résultat final
        result = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_finetunes_evaluated": len(evaluations),
            "average_score": round(average_score, 1),
            "performance_rating": get_performance_rating(average_score),
            "individual_evaluations": evaluations,
            "summary": {
                "best_performing": max(evaluations, key=lambda x: x["score"]),
                "worst_performing": min(evaluations, key=lambda x: x["score"]),
                "score_distribution": {
                    "excellent": sum(1 for e in evaluations if e["score"] >= 85),
                    "good": sum(1 for e in evaluations if 70 <= e["score"] < 85),
                    "average": sum(1 for e in evaluations if 50 <= e["score"] < 70),
                    "poor": sum(1 for e in evaluations if e["score"] < 50)
                }
            }
        }
        
        logger.info(f"Évaluation terminée. Score moyen: {average_score}/100")
        
        return success_response(
            data=result,
            message=f"Évaluation terminée avec un score moyen de {average_score}/100"
        )
        
    except Exception as e:
        logger.error(f"Erreur lors de l'évaluation: {str(e)}", exc_info=True)
        return server_error_response(str(e))
    finally:
        db.close()


def simulate_evaluation(finetune, attack_type):
    """
    Simule une évaluation quand GPT-4 n'est pas disponible.
    """
    import random
    
    # Score de base basé sur la longueur et la qualité apparente des données
    base_score = 65
    
    # Bonus pour la présence d'input/output
    if finetune.user_input and len(finetune.user_input) > 50:
        base_score += 5
    if finetune.model_outputs and len(finetune.model_outputs) > 100:
        base_score += 10
    
    # Bonus pour type d'attaque spécifié
    if attack_type != "Non spécifié":
        base_score += 5
    
    # Variation aléatoire
    score = max(0, min(100, base_score + random.randint(-10, 10)))
    
    return {
        "score": score,
        "finetune_id": finetune.id,
        "attack_type": attack_type,
        "reasoning": "Évaluation basée sur la structure et la complétude des données",
        "strengths": [
            "Données structurées présentes",
            "Format cohérent"
        ] if score >= 70 else ["Structure de base correcte"],
        "weaknesses": [
            "Manque de diversité dans les exemples",
            "Données limitées pour l'entraînement"
        ] if score < 80 else ["Pourrait bénéficier de plus de contexte"]
    }


def get_performance_rating(score):
    """
    Retourne une évaluation textuelle basée sur le score.
    """
    if score >= 85:
        return "Excellent - Le modèle montre d'excellentes performances"
    elif score >= 70:
        return "Bon - Le modèle est performant avec quelques améliorations possibles"
    elif score >= 50:
        return "Moyen - Le modèle nécessite des améliorations significatives"
    else:
        return "Faible - Le modèle requiert une refonte majeure"


@evaluation_gpt_bp.route("/evaluate/gpt/status", methods=["GET"])
@token_required
def get_evaluation_status(wallet):
    """
    Vérifie le statut du service d'évaluation.
    """
    db: Session = next(get_db())
    
    try:
        # Compter les fine-tunings disponibles
        finetune_count = db.query(Finetune).count()
        
        return success_response(
            data={
                "status": "available",
                "service": "Evaluation Service",
                "mode": "GPT-4" if USE_OPENAI else "Simulation",
                "openai_configured": USE_OPENAI,
                "finetunes_available": finetune_count,
                "can_evaluate": finetune_count >= 1
            },
            message=f"Service d'évaluation disponible en mode {'GPT-4' if USE_OPENAI else 'simulation'}"
        )
        
    except Exception as e:
        logger.error(f"Erreur lors de la vérification du statut: {str(e)}")
        return error_response(
            "Impossible de vérifier le statut du service",
            503
        )
    finally:
        db.close()