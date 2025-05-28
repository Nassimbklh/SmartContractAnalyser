from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Base

import os

DATABASE_URL = os.environ.get("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# Crée les tables à partir des modèles
Base.metadata.create_all(bind=engine)