from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.db.base import Base

class Firm(Base):
    __tablename__ = "firms"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

    clients = relationship("Client", back_populates="firm", cascade="all, delete-orphan")
