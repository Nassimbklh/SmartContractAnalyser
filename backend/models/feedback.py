from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base
import datetime
from datetime import UTC

class Feedback(Base):
    """
    Feedback model for storing user feedback on smart contract analysis reports.
    """
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    report_id = Column(Integer, ForeignKey("report.id"))
    status = Column(String)  # "OK" or "KO"
    comment = Column(Text, nullable=True)
    code_result = Column(Integer)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(UTC))

    # Relationships
    user = relationship("User", backref="feedbacks")
    report = relationship("Report", backref="feedbacks")

    def __repr__(self):
        return f"<Feedback(id={self.id}, user_id={self.user_id}, report_id={self.report_id}, status={self.status})>"
