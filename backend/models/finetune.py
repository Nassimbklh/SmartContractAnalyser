from sqlalchemy import Column, Integer, String, Text, ForeignKey, Float, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base


class Finetune(Base):
    __tablename__ = 'finetune'

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Contenu envoyé par l'utilisateur
    user_input = Column(Text, nullable=False)
    
    # Résultat généré par le modèle (lié à la table report)
    report_id = Column(Integer, ForeignKey('report.id'), nullable=True)
    model_outputs = Column(Text, nullable=False)
    
    # Métadonnées de l'utilisateur
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    user_info = Column(Text, nullable=True)
    
    # Feedback du user
    feedback_user = Column(Text, nullable=True)
    
    # Statut du retour utilisateur
    feedback_status = Column(String(50), nullable=True)  # pending, approved, rejected, etc.
    
    # Poids associé à la requête
    weight_request = Column(Float, default=1.0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relations
    report = relationship("Report", backref="finetune_entries")
    user = relationship("User", backref="finetune_entries")