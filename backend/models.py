from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True, index=True)
    wallet = Column(String, unique=True, index=True)
    hashed_password = Column(String)

class Report(Base):
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
    created_at = Column(DateTime, default=datetime.datetime.utcnow)