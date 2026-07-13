from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.database import Base, engine, SessionLocal
from app.models import *
from app.api.auth import router as auth_router
from app.api.company import router as company_router
from app.api.partners import router as partners_router
from app.api.accounts import router as accounts_router
from app.api.reports import router as reports_router
from app.api.vouchers import router as vouchers_router

app = FastAPI(title="AA-hub Backend")
app.include_router(auth_router)
app.include_router(company_router)
app.include_router(partners_router)
app.include_router(accounts_router)
app.include_router(reports_router)
app.include_router(vouchers_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

@app.get("/api/health")
def health():
    return {"status": "ok"}
