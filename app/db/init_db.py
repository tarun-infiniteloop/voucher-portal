from app.db.session import engine
from app.db.base import Base

# Import models so Base knows them
from app.models.user import User  # noqa: F401
# IMPORTANT: import ALL models here so Base.metadata knows them
from app.models.user import User  # noqa: F401
from app.models.firm import Firm  # noqa: F401
from app.models.client import Client  # noqa: F401
from app.models.voucher import Voucher  # noqa: F401
from app.models.voucher_comment import VoucherComment  # noqa: F401

def init_db():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()
    print("DB initialized ✅")
