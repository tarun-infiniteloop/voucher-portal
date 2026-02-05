from sqlalchemy import String, Integer, ForeignKey, DateTime
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

class Voucher(Base):
    __tablename__ = "vouchers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    firm_id: Mapped[int] = mapped_column(ForeignKey("firms.id"), nullable=False, index=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False, index=True)

    fy: Mapped[str] = mapped_column(String, nullable=False)        # e.g. "2025-26"
    month: Mapped[str] = mapped_column(String, nullable=False)     # e.g. "2026-02"
    vtype: Mapped[str] = mapped_column(String, nullable=False)     # PURCHASE/SALES/EXPENSE/BANK

    original_filename: Mapped[str] = mapped_column(String, nullable=False)
    stored_path: Mapped[str] = mapped_column(String, nullable=False)  # relative path under data/uploads

    status: Mapped[str] = mapped_column(String, nullable=False, default="RECEIVED")  # RECEIVED/QUERY/POSTED
    uploaded_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # optional metadata (v1 keeps minimal)
    amount: Mapped[int | None] = mapped_column(Integer, nullable=True)

    client = relationship("Client")
