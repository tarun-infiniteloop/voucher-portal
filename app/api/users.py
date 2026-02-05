from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.auth import get_current_user
from app.core.security import hash_password
from app.models.user import User
from app.models.client import Client

router = APIRouter(prefix="/users", tags=["users"])

class ClientUserCreate(BaseModel):
    client_id: int
    email: EmailStr
    full_name: str
    password: str  # later: send OTP / invite link

def require_admin(user: User):
    if user.role != "CA_ADMIN":
        raise HTTPException(status_code=403, detail="Admin only")

@router.post("/create-client-user")
def create_client_user(payload: ClientUserCreate, db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    require_admin(me)
    if not me.firm_id:
        raise HTTPException(status_code=400, detail="Create firm first")

    client = db.query(Client).filter(Client.id == payload.client_id, Client.firm_id == me.firm_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found in your firm")

    exists = db.query(User).filter(User.email == payload.email).first()
    if exists:
        raise HTTPException(status_code=400, detail="Email already exists")

    if len(payload.password) < 6:
        raise HTTPException(status_code=400, detail="Password too short")

    u = User(
        firm_id=me.firm_id,
        client_id=client.id,
        email=payload.email,
        full_name=payload.full_name,
        role="CLIENT",
        password_hash=hash_password(payload.password),
        is_active=1,
    )
    db.add(u)
    db.commit()
    db.refresh(u)

    return {"id": u.id, "email": u.email, "role": u.role, "client_id": u.client_id}
