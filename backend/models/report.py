from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .base import Base
import datetime
from datetime import UTC

class Report(Base):
    """
    Modèle de rapport pour stocker les rapports d'analyse de contrats intelligents.
    """
    __tablename__ = "report"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    filename = Column(String)
    status = Column(String)
    attack = Column(String)
    contract_name = Column(String)
    contract_address = Column(String)
    solc_version = Column(String)
    summary = Column(Text)
    reasoning = Column(Text)
    exploit_code = Column(Text)
    code_result = Column(Integer)
    contract_funding_success = Column(Boolean, default=False)
    attack_executed = Column(Boolean, default=False)
    attack_succeeded = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(UTC))

    def __repr__(self):
        return f"<Report(id={self.id}, filename={self.filename}, status={self.status})>"
