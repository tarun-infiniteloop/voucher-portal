from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from pathlib import Path

from app.db.session import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.client import Client
from app.models.voucher import Voucher
from app.services.storage import build_voucher_path

router = APIRouter(prefix="/vouchers", tags=["vouchers"])

ALLOWED_TYPES = {"PURCHASE", "SALES", "EXPENSE", "BANK"}

@router.post("/upload")
async def upload_voucher(
    fy: str = Form(...),
    month: str = Form(...),
    vtype: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    me: User = Depends(get_current_user),
):
    if not me.firm_id:
        raise HTTPException(status_code=400, detail="User not linked to a firm")

    if me.role != "CLIENT":
        raise HTTPException(status_code=403, detail="Only CLIENT users can upload vouchers")
    
    if not me.client_id:
        raise HTTPException(status_code=400, detail="Client user not linked to a client")


    vtype = vtype.upper().strip()
    if vtype not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid vtype. Allowed: {sorted(ALLOWED_TYPES)}")

    client = db.query(Client).filter(Client.id == me.client_id, Client.firm_id == me.firm_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found for your firm")

    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")

    path: Path = build_voucher_path(
        firm_id=me.firm_id,
        client_code=client.code,
        fy=fy,
        month=month,
        vtype=vtype,
        original_filename=file.filename,
    )
    path.parent.mkdir(parents=True, exist_ok=True)

    # save file
    contents = await file.read()
    path.write_bytes(contents)

    v = Voucher(
        firm_id=me.firm_id,
        client_id=client.id,
        fy=fy,
        month=month,
        vtype=vtype,
        original_filename=file.filename,
        stored_path=str(path.as_posix()),
        status="RECEIVED",
        uploaded_by_user_id=me.id,
    )
    db.add(v)
    db.commit()
    db.refresh(v)

    return {"id": v.id, "status": v.status, "stored_path": v.stored_path}

@router.get("")
def list_vouchers(
    client_id: int | None = None,
    fy: str | None = None,
    month: str | None = None,
    vtype: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    me: User = Depends(get_current_user),
):
    if not me.firm_id:
        return {"vouchers": []}

    q = db.query(Voucher).filter(Voucher.firm_id == me.firm_id)

    if client_id is not None:
        q = q.filter(Voucher.client_id == client_id)
    if fy is not None:
        q = q.filter(Voucher.fy == fy)
    if month is not None:
        q = q.filter(Voucher.month == month)
    if vtype is not None:
        q = q.filter(Voucher.vtype == vtype.upper().strip())
    if status is not None:
        q = q.filter(Voucher.status == status.upper().strip())

    rows = q.order_by(Voucher.id.desc()).limit(200).all()
    return {
        "vouchers": [
            {
                "id": r.id,
                "client_id": r.client_id,
                "fy": r.fy,
                "month": r.month,
                "vtype": r.vtype,
                "status": r.status,
                "original_filename": r.original_filename,
                "stored_path": r.stored_path,
                "uploaded_by_user_id": r.uploaded_by_user_id,
                "uploaded_at": r.uploaded_at.isoformat() if r.uploaded_at else None,
            }
            for r in rows
        ]
    }
