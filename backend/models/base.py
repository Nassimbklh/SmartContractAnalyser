from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Créer la base SQLAlchemy
Base = declarative_base()

# Obtenir l'URL de la base de données depuis la variable d'environnement
DATABASE_URL = os.environ.get("DATABASE_URL")

# Créer le moteur et la session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def get_db():
    """
    Obtenir une session de base de données.

    Returns:
        Session: Une session SQLAlchemy.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
