from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pathlib import Path
from io import BytesIO
import zipfile
from datetime import datetime

from app.db.session import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.voucher import Voucher
from app.models.client import Client

router = APIRouter(prefix="/reports", tags=["reports"])

UPLOAD_ROOT = Path("data/uploads").resolve()

def safe_resolve(p: str) -> Path:
    """Prevent path traversal: ensure file is inside data/uploads."""
    fp = Path(p).resolve()
    if UPLOAD_ROOT not in fp.parents and fp != UPLOAD_ROOT:
        raise HTTPException(status_code=400, detail="Invalid stored_path outside uploads")
    return fp

@router.get("/vouchers-zip")
def vouchers_zip(
    fy: str,
    month: str,
    client_id: int | None = None,
    vtype: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    me: User = Depends(get_current_user),
):
    if not me.firm_id:
        raise HTTPException(status_code=400, detail="User not linked to a firm")

    # Role rules
    if me.role == "CLIENT":
        if not me.client_id:
            raise HTTPException(status_code=400, detail="Client user not linked to a client")
        client_id = me.client_id  # force
    else:
        # CA roles: require a client_id for MVP (keeps it simple)
        if client_id is None:
            raise HTTPException(status_code=400, detail="client_id is required for CA users")

    # Verify client belongs to firm
    client = db.query(Client).filter(Client.id == client_id, Client.firm_id == me.firm_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found for your firm")

    q = db.query(Voucher).filter(
        Voucher.firm_id == me.firm_id,
        Voucher.client_id == client_id,
        Voucher.fy == fy,
        Voucher.month == month,
    )

    if vtype:
        q = q.filter(Voucher.vtype == vtype.upper().strip())
    if status:
        q = q.filter(Voucher.status == status.upper().strip())

    rows = q.order_by(Voucher.id.asc()).all()
    if not rows:
        raise HTTPException(status_code=404, detail="No vouchers found for given filters")

    # Build ZIP in memory (MVP)
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for r in rows:
            fp = safe_resolve(r.stored_path)
            if not fp.exists():
                # skip missing files but keep a note
                z.writestr(f"_MISSING_FILES/{r.id}.txt", f"Missing on disk: {r.stored_path}")
                continue

            # Nice inside-zip naming:
            # PURCHASE/20260205_...pdf
            arcname = f"{r.vtype}/{fp.name}"
            z.write(fp, arcname=arcname)

        # Add a small manifest
        z.writestr(
            "manifest.txt",
            "\n".join([
                f"firm_id={me.firm_id}",
                f"client_id={client_id}",
                f"client_code={client.code}",
                f"fy={fy}",
                f"month={month}",
                f"vtype={vtype or ''}",
                f"status={status or ''}",
                f"generated_at={datetime.utcnow().isoformat()}Z",
                f"count_db={len(rows)}",
            ])
        )

    buf.seek(0)

    filename = f"vouchers_{client.code}_{fy}_{month}"
    if vtype:
        filename += f"_{vtype.upper().strip()}"
    if status:
        filename += f"_{status.upper().strip()}"
    filename += ".zip"

    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return StreamingResponse(buf, media_type="application/zip", headers=headers)
