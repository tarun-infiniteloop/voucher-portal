from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.voucher import Voucher
from app.models.voucher_comment import VoucherComment

router = APIRouter(prefix="/vouchers", tags=["voucher-workflow"])

ALLOWED_STATUSES = {"RECEIVED", "QUERY", "POSTED"}

class CommentCreate(BaseModel):
    message: str

class StatusUpdate(BaseModel):
    status: str

def require_firm(me: User):
    if not me.firm_id:
        raise HTTPException(status_code=400, detail="User not linked to a firm")

def get_voucher_or_404(db: Session, me: User, voucher_id: int) -> Voucher:
    v = db.query(Voucher).filter(Voucher.id == voucher_id, Voucher.firm_id == me.firm_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Voucher not found")
    return v

@router.get("/by-id/{voucher_id}")
def voucher_detail(voucher_id: int, db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    require_firm(me)
    v = get_voucher_or_404(db, me, voucher_id)

    comments = (
        db.query(VoucherComment)
        .filter(VoucherComment.voucher_id == voucher_id)
        .order_by(VoucherComment.id.asc())
        .all()
    )

    return {
        "voucher": {
            "id": v.id,
            "client_id": v.client_id,
            "fy": v.fy,
            "month": v.month,
            "vtype": v.vtype,
            "status": v.status,
            "original_filename": v.original_filename,
            "stored_path": v.stored_path,
        },
        "comments": [
            {
                "id": c.id,
                "user_id": c.user_id,
                "message": c.message,
                "created_at": c.created_at.isoformat(),
            }
            for c in comments
        ],
    }

@router.post("/{voucher_id}/comment")
def add_comment(voucher_id: int, payload: CommentCreate, db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    require_firm(me)
    v = get_voucher_or_404(db, me, voucher_id)

    msg = payload.message.strip()
    if not msg:
        raise HTTPException(status_code=400, detail="Empty message")

    c = VoucherComment(voucher_id=v.id, user_id=me.id, message=msg)
    db.add(c)

    # Simple workflow rule:
    # If CA admin/staff comments, mark voucher as QUERY (unless already POSTED)
    if me.role in ("CA_ADMIN", "CA_STAFF") and v.status != "POSTED":
        v.status = "QUERY"
        db.add(v)

    db.commit()
    db.refresh(c)

    return {"comment_id": c.id, "voucher_status": v.status}

@router.patch("/{voucher_id}/status")
def update_status(voucher_id: int, payload: StatusUpdate, db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    require_firm(me)
    v = get_voucher_or_404(db, me, voucher_id)

    # Only CA can change status explicitly
    if me.role not in ("CA_ADMIN", "CA_STAFF"):
        raise HTTPException(status_code=403, detail="Only CA can update status")

    new_status = payload.status.upper().strip()
    if new_status not in ALLOWED_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status. Allowed: {sorted(ALLOWED_STATUSES)}")

    v.status = new_status
    db.add(v)
    db.commit()
    return {"id": v.id, "status": v.status}
