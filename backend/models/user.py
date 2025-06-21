from sqlalchemy import Column, Integer, String, Float
from .base import Base

class User(Base):
    """
    Modèle utilisateur pour stocker les informations des utilisateurs.
    """
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    wallet = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    technical_score = Column(Float, nullable=True)
    technical_level = Column(String, nullable=True)

    def __repr__(self):
        return f"<User(id={self.id}, wallet={self.wallet})>"
