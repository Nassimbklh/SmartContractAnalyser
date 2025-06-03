from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base
import datetime
from datetime import UTC

class Report(Base):
    """
    Report model for storing smart contract analysis reports.
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
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(UTC))
    
    def __repr__(self):
        return f"<Report(id={self.id}, filename={self.filename}, status={self.status})>"