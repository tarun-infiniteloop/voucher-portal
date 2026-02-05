from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

class Client(Base):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    firm_id: Mapped[int] = mapped_column(ForeignKey("firms.id"), nullable=False, index=True)

    name: Mapped[str] = mapped_column(String, nullable=False)
    code: Mapped[str] = mapped_column(String, nullable=False)  # short unique code per firm

    firm = relationship("Firm")
