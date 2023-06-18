from sqlalchemy import Column, Integer, String, Sequence
from database import connector

class Paper(connector.Manager.Base):
    __tablename__ = 'papers'
    id = Column(String(20), primary_key=True)
    abstract = Column(String(1500))
    abstract_idx = Column(String(1500))