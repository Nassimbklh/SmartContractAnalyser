from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class AnalysisStatus(Base):
    """
    Modèle pour stocker le statut d'analyse d'un contrat intelligent.
    """
    __tablename__ = "analysis_status"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("report.id"), nullable=True)
    format_check = Column(String, default="pending")
    compilation = Column(String, default="pending")
    function_analysis = Column(String, default="pending")
    vulnerability_scan = Column(String, default="pending")
    report_generation = Column(String, default="pending")

    # Relationship with Report model
    report = relationship("Report", back_populates="analysis_status")

    def __repr__(self):
        return f"<AnalysisStatus(id={self.id}, report_id={self.report_id})>"