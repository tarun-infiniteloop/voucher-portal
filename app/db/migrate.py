from app.db.session import engine
from app.db.base import Base

from app.models.user import User  # noqa
from app.models.firm import Firm  # noqa
from app.models.client import Client  # noqa
from app.models.voucher import Voucher  # noqa
from app.models.voucher_comment import VoucherComment  # noqa

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    print("Migration applied ✅")
