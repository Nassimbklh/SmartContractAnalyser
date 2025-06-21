from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint, Float
from sqlalchemy.orm import relationship
from .base import Base
import datetime
from datetime import UTC

class Feedback(Base):
    """
    Modèle de retour pour stocker les retours des utilisateurs sur les rapports d'analyse de contrats intelligents.
    """
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    report_id = Column(Integer, ForeignKey("report.id"))
    status = Column(String)  # "OK" ou "KO"
    comment = Column(Text, nullable=True)
    code_result = Column(Integer)
    weight_request = Column(Float)  # Poids calculé en fonction de code_result et technical_score de l'utilisateur
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(UTC))

    # Ajouter une contrainte unique pour garantir un seul retour par utilisateur par rapport
    __table_args__ = (
        UniqueConstraint('user_id', 'report_id', name='uix_user_report'),
        {
            'sqlite_autoincrement': True,
            'mysql_engine': 'InnoDB',
            'mysql_charset': 'utf8mb4',
            'extend_existing': True
        }
    )

    # Relations
    user = relationship("User", backref="feedbacks")
    report = relationship("Report", backref="feedbacks")

    def __repr__(self):
        return f"<Feedback(id={self.id}, user_id={self.user_id}, report_id={self.report_id}, status={self.status}, weight_request={self.weight_request})>"
