from flask import Blueprint, request, jsonify
from sqlalchemy.orm import Session
from models import get_db, Finetune, User, Report
from utils import (
    token_required, success_response, error_response,
    not_found_response, server_error_response
)
from pydantic import BaseModel, Field, ValidationError
from typing import Optional
import logging

logger = logging.getLogger(__name__)
finetune_bp = Blueprint('finetune', __name__)


# Pydantic models for validation
class FinetuneCreateRequest(BaseModel):
    user_input: str = Field(..., min_length=1, description="Contenu envoyé par l'utilisateur")
    model_outputs: str = Field(..., min_length=1, description="Résultat généré par le modèle")
    report_id: Optional[int] = Field(None, description="ID du rapport lié")
    user_info: Optional[str] = Field(None, description="Métadonnées de l'utilisateur")
    feedback_user: Optional[str] = Field(None, description="Feedback du user")
    feedback_status: Optional[str] = Field(None, pattern="^(pending|approved|rejected|under_review)$", 
                                          description="Statut du retour utilisateur")
    weight_request: Optional[float] = Field(1.0, ge=0.0, le=10.0, description="Poids associé à la requête")


class FinetuneUpdateRequest(BaseModel):
    feedback_user: Optional[str] = Field(None, description="Feedback du user")
    feedback_status: Optional[str] = Field(None, pattern="^(pending|approved|rejected|under_review)$", 
                                          description="Statut du retour utilisateur")
    weight_request: Optional[float] = Field(None, ge=0.0, le=10.0, description="Poids associé à la requête")


@finetune_bp.route("/finetune", methods=["POST"])
@token_required
def create_finetune(wallet):
    """
    Créer une nouvelle entrée finetune.
    
    Corps de la requête:
        user_input (str): Contenu envoyé par l'utilisateur
        model_outputs (str): Résultat généré par le modèle
        report_id (int, optional): ID du rapport lié
        user_info (str, optional): Métadonnées de l'utilisateur
        feedback_user (str, optional): Feedback du user
        feedback_status (str, optional): Statut du retour utilisateur
        weight_request (float, optional): Poids associé à la requête
    
    Returns:
        JSON: Une réponse de succès avec l'ID de l'entrée créée.
    """
    logger.info(f"Création d'une entrée finetune depuis le portefeuille: {wallet}")
    
    try:
        # Valider les données avec Pydantic
        data = request.json
        validated_data = FinetuneCreateRequest(**data)
    except ValidationError as e:
        logger.warning(f"Validation échouée: {e.errors()}")
        return error_response(f"Données invalides: {e.errors()}", 400)
    except Exception as e:
        logger.warning(f"Erreur lors de la récupération des données: {str(e)}")
        return error_response("Données invalides", 400)
    
    db: Session = next(get_db())
    try:
        # Récupérer l'utilisateur
        user = db.query(User).filter(User.wallet == wallet).first()
        if not user:
            logger.warning(f"Utilisateur non trouvé pour le portefeuille: {wallet}")
            return not_found_response("Utilisateur non trouvé")
        
        # Vérifier si le report_id existe si fourni
        if validated_data.report_id:
            report = db.query(Report).filter(Report.id == validated_data.report_id).first()
            if not report:
                logger.warning(f"Rapport non trouvé avec l'ID: {validated_data.report_id}")
                return not_found_response("Rapport introuvable")
        
        # Créer l'entrée finetune
        finetune = Finetune(
            user_input=validated_data.user_input,
            model_outputs=validated_data.model_outputs,
            report_id=validated_data.report_id,
            user_id=user.id,
            user_info=validated_data.user_info,
            feedback_user=validated_data.feedback_user,
            feedback_status=validated_data.feedback_status or "pending",
            weight_request=validated_data.weight_request
        )
        
        db.add(finetune)
        db.commit()
        db.refresh(finetune)
        
        logger.info(f"Entrée finetune créée avec ID: {finetune.id}")
        
        return success_response(
            data={"finetune_id": finetune.id},
            message="Entrée finetune créée avec succès"
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Erreur lors de la création de l'entrée finetune: {str(e)}", exc_info=True)
        return server_error_response(str(e))
    finally:
        db.close()


@finetune_bp.route("/finetune/<int:finetune_id>", methods=["GET"])
@token_required
def get_finetune(wallet, finetune_id):
    """
    Récupérer une entrée finetune par ID.
    
    Args:
        finetune_id (int): L'ID de l'entrée finetune
    
    Returns:
        JSON: Les détails de l'entrée finetune
    """
    logger.info(f"Récupération de l'entrée finetune {finetune_id} depuis le portefeuille: {wallet}")
    
    db: Session = next(get_db())
    try:
        # Récupérer l'utilisateur
        user = db.query(User).filter(User.wallet == wallet).first()
        if not user:
            logger.warning(f"Utilisateur non trouvé pour le portefeuille: {wallet}")
            return not_found_response("Utilisateur non trouvé")
        
        # Récupérer l'entrée finetune
        finetune = db.query(Finetune).filter(
            Finetune.id == finetune_id,
            Finetune.user_id == user.id
        ).first()
        
        if not finetune:
            logger.warning(f"Entrée finetune non trouvée avec l'ID: {finetune_id}")
            return not_found_response("Entrée finetune introuvable")
        
        return success_response(data={
            "id": finetune.id,
            "user_input": finetune.user_input,
            "model_outputs": finetune.model_outputs,
            "report_id": finetune.report_id,
            "user_info": finetune.user_info,
            "feedback_user": finetune.feedback_user,
            "feedback_status": finetune.feedback_status,
            "weight_request": finetune.weight_request,
            "created_at": finetune.created_at.isoformat() if finetune.created_at else None,
            "updated_at": finetune.updated_at.isoformat() if finetune.updated_at else None
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de l'entrée finetune: {str(e)}", exc_info=True)
        return server_error_response(str(e))
    finally:
        db.close()


@finetune_bp.route("/finetune/<int:finetune_id>", methods=["PUT"])
@token_required
def update_finetune(wallet, finetune_id):
    """
    Mettre à jour une entrée finetune existante.
    
    Args:
        finetune_id (int): L'ID de l'entrée finetune
    
    Corps de la requête:
        feedback_user (str, optional): Feedback du user
        feedback_status (str, optional): Statut du retour utilisateur
        weight_request (float, optional): Poids associé à la requête
    
    Returns:
        JSON: Une réponse de succès
    """
    logger.info(f"Mise à jour de l'entrée finetune {finetune_id} depuis le portefeuille: {wallet}")
    
    try:
        # Valider les données avec Pydantic
        data = request.json
        validated_data = FinetuneUpdateRequest(**data)
    except ValidationError as e:
        logger.warning(f"Validation échouée: {e.errors()}")
        return error_response(f"Données invalides: {e.errors()}", 400)
    except Exception as e:
        logger.warning(f"Erreur lors de la récupération des données: {str(e)}")
        return error_response("Données invalides", 400)
    
    db: Session = next(get_db())
    try:
        # Récupérer l'utilisateur
        user = db.query(User).filter(User.wallet == wallet).first()
        if not user:
            logger.warning(f"Utilisateur non trouvé pour le portefeuille: {wallet}")
            return not_found_response("Utilisateur non trouvé")
        
        # Récupérer l'entrée finetune
        finetune = db.query(Finetune).filter(
            Finetune.id == finetune_id,
            Finetune.user_id == user.id
        ).first()
        
        if not finetune:
            logger.warning(f"Entrée finetune non trouvée avec l'ID: {finetune_id}")
            return not_found_response("Entrée finetune introuvable")
        
        # Mettre à jour les champs
        if validated_data.feedback_user is not None:
            finetune.feedback_user = validated_data.feedback_user
        if validated_data.feedback_status is not None:
            finetune.feedback_status = validated_data.feedback_status
        if validated_data.weight_request is not None:
            finetune.weight_request = validated_data.weight_request
        
        db.commit()
        
        logger.info(f"Entrée finetune {finetune_id} mise à jour avec succès")
        
        return success_response(message="Entrée finetune mise à jour avec succès")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Erreur lors de la mise à jour de l'entrée finetune: {str(e)}", exc_info=True)
        return server_error_response(str(e))
    finally:
        db.close()


@finetune_bp.route("/finetune", methods=["GET"])
@token_required
def list_finetune(wallet):
    """
    Lister toutes les entrées finetune de l'utilisateur.
    
    Query parameters:
        page (int, optional): Numéro de page (défaut: 1)
        per_page (int, optional): Nombre d'éléments par page (défaut: 10)
        feedback_status (str, optional): Filtrer par statut de feedback
    
    Returns:
        JSON: Liste des entrées finetune avec pagination
    """
    logger.info(f"Listing des entrées finetune depuis le portefeuille: {wallet}")
    
    # Paramètres de pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    feedback_status = request.args.get('feedback_status', type=str)
    
    # Validation des paramètres
    if page < 1:
        return error_response("Le numéro de page doit être >= 1", 400)
    if per_page < 1 or per_page > 100:
        return error_response("Le nombre d'éléments par page doit être entre 1 et 100", 400)
    
    db: Session = next(get_db())
    try:
        # Récupérer l'utilisateur
        user = db.query(User).filter(User.wallet == wallet).first()
        if not user:
            logger.warning(f"Utilisateur non trouvé pour le portefeuille: {wallet}")
            return not_found_response("Utilisateur non trouvé")
        
        # Construire la requête
        query = db.query(Finetune).filter(Finetune.user_id == user.id)
        
        if feedback_status:
            query = query.filter(Finetune.feedback_status == feedback_status)
        
        # Pagination
        total = query.count()
        finetunes = query.order_by(Finetune.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
        
        return success_response(data={
            "items": [{
                "id": f.id,
                "user_input": f.user_input,
                "model_outputs": f.model_outputs,
                "report_id": f.report_id,
                "user_info": f.user_info,
                "feedback_user": f.feedback_user,
                "feedback_status": f.feedback_status,
                "weight_request": f.weight_request,
                "created_at": f.created_at.isoformat() if f.created_at else None,
                "updated_at": f.updated_at.isoformat() if f.updated_at else None
            } for f in finetunes],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "pages": (total + per_page - 1) // per_page
            }
        })
        
    except Exception as e:
        logger.error(f"Erreur lors du listing des entrées finetune: {str(e)}", exc_info=True)
        return server_error_response(str(e))
    finally:
        db.close()