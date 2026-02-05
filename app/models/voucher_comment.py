from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

class VoucherComment(Base):
    __tablename__ = "voucher_comments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    voucher_id: Mapped[int] = mapped_column(ForeignKey("vouchers.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    message: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
