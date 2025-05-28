from sqlalchemy import Column, Integer, String
from .base import Base

class User(Base):
    """
    User model for storing user information.
    """
    __tablename__ = "user"
    
    id = Column(Integer, primary_key=True, index=True)
    wallet = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    
    def __repr__(self):
        return f"<User(id={self.id}, wallet={self.wallet})>"