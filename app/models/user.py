from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    firm_id: Mapped[int | None] = mapped_column(ForeignKey("firms.id"), nullable=True, index=True)

    client_id: Mapped[int | None] = mapped_column(ForeignKey("clients.id"), nullable=True, index=True)
    # client_id only for role=CLIENT. CA roles keep it None.

    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[int] = mapped_column(default=1)