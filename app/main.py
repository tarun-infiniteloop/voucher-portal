from fastapi import FastAPI
from app.api.auth import router as auth_router
from app.api.firm import router as firm_router
from app.api.voucher import router as voucher_router
from app.api.voucher_workflow import router as voucher_workflow_router
from app.api.users import router as users_router
from app.api.voucher_summary import router as voucher_summary_router
from app.api.voucher_export import router as voucher_export_router

app = FastAPI(title="Voucher Portal")

@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(auth_router)
app.include_router(firm_router)
app.include_router(voucher_router)
app.include_router(voucher_workflow_router)
app.include_router(users_router)
app.include_router(voucher_summary_router)
app.include_router(voucher_export_router)
