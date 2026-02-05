from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.core.security import hash_password

from app.models.user import User
from app.models.firm import Firm  # noqa: F401
from app.models.client import Client  # noqa: F401

def seed():
    db: Session = SessionLocal()
    try:
        email = "admin@cadsk.local"
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            print("Admin already exists ✅")
            return

        u = User(
            email=email,
            full_name="CA Admin",
            role="CA_ADMIN",
            password_hash=hash_password("admin123"),
            is_active=1,
        )
        db.add(u)
        db.commit()
        print("Seeded admin ✅  email=admin@cadsk.local password=admin123")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
