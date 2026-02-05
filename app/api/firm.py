from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.firm import Firm
from app.models.client import Client
from app.models.user import User
from app.api.auth import get_current_user

router = APIRouter(prefix="/firm", tags=["firm"])

class FirmCreate(BaseModel):
    name: str

class ClientCreate(BaseModel):
    name: str
    code: str

def require_admin(user: User):
    if user.role != "CA_ADMIN":
        raise HTTPException(status_code=403, detail="Admin only")

@router.post("")
def create_firm(payload: FirmCreate, db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    require_admin(me)

    firm = Firm(name=payload.name)
    db.add(firm)
    db.commit()
    db.refresh(firm)

    # attach admin to this firm
    me.firm_id = firm.id
    db.add(me)
    db.commit()

    return {"id": firm.id, "name": firm.name}

@router.get("")
def get_my_firm(db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    if not me.firm_id:
        return {"firm": None}

    firm = db.query(Firm).filter(Firm.id == me.firm_id).first()
    return {"firm": {"id": firm.id, "name": firm.name}}

@router.post("/clients")
def create_client(payload: ClientCreate, db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    require_admin(me)
    if not me.firm_id:
        raise HTTPException(status_code=400, detail="Create firm first")

    exists = db.query(Client).filter(
        Client.firm_id == me.firm_id,
        Client.code == payload.code
    ).first()
    if exists:
        raise HTTPException(status_code=400, detail="Client code already exists for this firm")

    c = Client(firm_id=me.firm_id, name=payload.name, code=payload.code)
    db.add(c)
    db.commit()
    db.refresh(c)
    return {"id": c.id, "firm_id": c.firm_id, "name": c.name, "code": c.code}

@router.get("/clients")
def list_clients(db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    if not me.firm_id:
        return {"clients": []}
    clients = db.query(Client).filter(Client.firm_id == me.firm_id).order_by(Client.id.desc()).all()
    return {"clients": [{"id": c.id, "name": c.name, "code": c.code} for c in clients]}
