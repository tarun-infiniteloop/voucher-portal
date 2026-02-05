from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.voucher import Voucher

router = APIRouter(prefix="/reports", tags=["reports"])

@router.get("/stats")
def voucher_summary(
    fy: str | None = None,
    month: str | None = None,
    client_id: int | None = None,
    db: Session = Depends(get_db),
    me: User = Depends(get_current_user),
):
    if not me.firm_id:
        return {"summary": []}

    q = db.query(
        Voucher.vtype.label("vtype"),
        Voucher.status.label("status"),
        func.count(Voucher.id).label("count"),
    ).filter(Voucher.firm_id == me.firm_id)

    # CLIENT can only see their own data
    if me.role == "CLIENT":
        if not me.client_id:
            return {"summary": []}
        q = q.filter(Voucher.client_id == me.client_id)
    else:
        # CA roles can optionally filter by client_id
        if client_id is not None:
            q = q.filter(Voucher.client_id == client_id)

    if fy is not None:
        q = q.filter(Voucher.fy == fy)
    if month is not None:
        q = q.filter(Voucher.month == month)

    rows = q.group_by(Voucher.vtype, Voucher.status).all()

    # reshape to:
    # {vtype: {status: count, ...}, ...}
    out = {}
    for r in rows:
        out.setdefault(r.vtype, {})
        out[r.vtype][r.status] = r.count

    # also compute totals per type
    summary = []
    for vtype, by_status in sorted(out.items()):
        total = sum(by_status.values())
        summary.append({"vtype": vtype, "total": total, "by_status": by_status})

    return {"fy": fy, "month": month, "client_id": client_id if me.role != "CLIENT" else me.client_id, "summary": summary}
