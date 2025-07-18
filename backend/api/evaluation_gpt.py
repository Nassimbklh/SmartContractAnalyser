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

# Note: Pour cette version simplifiée, on simule l'évaluation GPT-4
# Dans un environnement de production, vous devriez utiliser l'API OpenAI

@evaluation_gpt_bp.route("/evaluate/gpt", methods=["POST"])
@token_required
def evaluate_with_gpt(wallet):
    """
    Évalue les 10 derniers fine-tunings en simulant GPT-4.
    
    Returns:
        JSON: Note moyenne et détails de l'évaluation
    """
    logger.info(f"Lancement de l'évaluation simulée depuis le portefeuille: {wallet}")
    
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
            
            if finetune.report:
                try:
                    if finetune.report.results:
                        report_data = json.loads(finetune.report.results) if isinstance(finetune.report.results, str) else finetune.report.results
                        # Extraire le type depuis le rapport
                        if isinstance(report_data, dict):
                            attack_type = report_data.get('vulnerability', report_data.get('attack_type', 'Non spécifié'))
                except Exception as e:
                    logger.warning(f"Erreur parsing rapport: {e}")
            
            # Simuler une évaluation basée sur les données disponibles
            base_score = 70  # Score de base
            
            # Ajuster selon le feedback
            if finetune.feedback_status == "approved":
                base_score += 15
            elif finetune.feedback_status == "rejected":
                base_score -= 10
            
            # Ajuster selon la présence de feedback utilisateur
            if finetune.feedback_user:
                base_score += 5
            
            # Ajouter un peu de variation
            import random
            score = max(0, min(100, base_score + random.randint(-10, 10)))
            
            # Créer l'évaluation
            evaluation = {
                "score": score,
                "finetune_id": finetune.id,
                "attack_type": attack_type,
                "reasoning": f"Évaluation basée sur le feedback '{finetune.feedback_status or 'pending'}' et la qualité des données",
                "strengths": [
                    "Données d'entrée bien structurées",
                    "Modèle répond de manière cohérente"
                ] if score >= 70 else ["Structure de base correcte"],
                "weaknesses": [
                    "Manque de diversité dans les exemples",
                    "Feedback utilisateur limité"
                ] if score < 80 else ["Pourrait bénéficier de plus de données"]
            }
            
            evaluations.append(evaluation)
            total_score += score
            
            logger.info(f"Fine-tuning {finetune.id} évalué: {score}/100")
        
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
    finally:
        db.close()