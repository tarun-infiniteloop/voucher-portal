# from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
# from sqlalchemy.orm import Mapped, mapped_column, relationship

# from app.db.base import Base

# class Client(Base):
#     __tablename__ = "clients"

#     id: Mapped[int] = mapped_column(primary_key=True, index=True)
#     firm_id: Mapped[int] = mapped_column(ForeignKey("firms.id"), nullable=False, index=True)

#     name: Mapped[str] = mapped_column(String, nullable=False)
#     code: Mapped[str] = mapped_column(String, nullable=False)  # short unique code per firm

#     firm = relationship("Firm")


from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.base import Base


class Client(Base):
    __tablename__ = "clients"

    __table_args__ = (
        UniqueConstraint("firm_id", "code", name="uq_client_firm_code"),
    )

    id = Column(Integer, primary_key=True)
    firm_id = Column(Integer, ForeignKey("firms.id"), nullable=False)

    name = Column(String, nullable=False)
    code = Column(String, nullable=False)

    firm = relationship("Firm", back_populates="clients")
