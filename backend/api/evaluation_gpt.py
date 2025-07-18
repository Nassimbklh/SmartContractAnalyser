from flask import Blueprint, request, jsonify
from utils import token_required, success_response, error_response, server_error_response
from database import db
from models import Finetune, FeedbackData
import logging
import os
from openai import OpenAI
from datetime import datetime
import json

logger = logging.getLogger(__name__)
evaluation_gpt_bp = Blueprint('evaluation_gpt', __name__)

# Configuration OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@evaluation_gpt_bp.route("/evaluate/gpt", methods=["POST"])
@token_required
def evaluate_with_gpt(wallet):
    """
    Évalue les 10 derniers fine-tunings en utilisant GPT-4.
    
    Returns:
        JSON: Note moyenne et détails de l'évaluation
    """
    logger.info(f"Lancement de l'évaluation GPT-4 depuis le portefeuille: {wallet}")
    
    try:
        # Récupérer les 10 derniers fine-tunings avec leurs feedbacks
        recent_finetunes = db.query(Finetune).order_by(Finetune.created_at.desc()).limit(10).all()
        
        if not recent_finetunes:
            return error_response("Aucun fine-tuning trouvé", 404)
        
        evaluations = []
        total_score = 0
        
        for finetune in recent_finetunes:
            # Récupérer les feedbacks associés
            feedbacks = db.query(FeedbackData).filter(FeedbackData.finetune_id == finetune.id).all()
            
            # Préparer les données pour l'évaluation
            finetune_data = {
                "id": finetune.id,
                "created_at": finetune.created_at.isoformat(),
                "attack_type": finetune.attack_type,
                "vulnerability_type": finetune.vulnerability_type,
                "feedbacks": [
                    {
                        "is_positive": fb.is_positive,
                        "comment": fb.comment,
                        "created_at": fb.created_at.isoformat()
                    }
                    for fb in feedbacks
                ]
            }
            
            # Créer le prompt pour GPT-4
            prompt = f"""
            Évalue ce fine-tuning d'un modèle spécialisé dans l'analyse de smart contracts Solidity.
            
            Données du fine-tuning:
            - Type d'attaque: {finetune.attack_type}
            - Type de vulnérabilité: {finetune.vulnerability_type}
            - Date: {finetune.created_at}
            - Nombre de feedbacks: {len(feedbacks)}
            - Feedbacks positifs: {sum(1 for fb in feedbacks if fb.is_positive)}
            - Feedbacks négatifs: {sum(1 for fb in feedbacks if not fb.is_positive)}
            
            Commentaires des utilisateurs:
            {json.dumps([fb['comment'] for fb in finetune_data['feedbacks'] if fb['comment']], indent=2)}
            
            Évalue la qualité de ce fine-tuning sur une échelle de 0 à 100 en considérant:
            1. La pertinence du type d'attaque ciblé (20%)
            2. La cohérence des feedbacks utilisateurs (30%)
            3. Le ratio feedbacks positifs/négatifs (30%)
            4. La qualité des commentaires et leur utilité (20%)
            
            Réponds uniquement avec un JSON contenant:
            {{
                "score": <number entre 0 et 100>,
                "reasoning": "<explication courte de la note>",
                "strengths": ["<point fort 1>", "<point fort 2>"],
                "weaknesses": ["<point faible 1>", "<point faible 2>"]
            }}
            """
            
            # Appeler GPT-4
            response = client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "Tu es un expert en sécurité des smart contracts et en évaluation de modèles ML."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            # Parser la réponse
            evaluation = json.loads(response.choices[0].message.content)
            evaluation["finetune_id"] = finetune.id
            evaluation["attack_type"] = finetune.attack_type
            
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
        
        logger.info(f"Évaluation GPT-4 terminée. Score moyen: {average_score}/100")
        
        return success_response(
            data=result,
            message=f"Évaluation terminée avec un score moyen de {average_score}/100"
        )
        
    except Exception as e:
        logger.error(f"Erreur lors de l'évaluation GPT-4: {str(e)}", exc_info=True)
        return server_error_response(str(e))


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
    Vérifie le statut du service d'évaluation GPT-4.
    """
    try:
        # Vérifier si l'API key est configurée
        if not os.getenv("OPENAI_API_KEY"):
            return error_response(
                "Service d'évaluation non configuré",
                503
            )
        
        # Compter les fine-tunings disponibles
        finetune_count = db.query(Finetune).count()
        
        return success_response(
            data={
                "status": "available",
                "service": "GPT-4 Evaluation",
                "finetunes_available": finetune_count,
                "can_evaluate": finetune_count >= 1
            },
            message="Service d'évaluation disponible"
        )
        
    except Exception as e:
        logger.error(f"Erreur lors de la vérification du statut: {str(e)}")
        return error_response(
            "Impossible de vérifier le statut du service",
            503
        )