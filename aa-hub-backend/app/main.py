from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.database import Base, engine, SessionLocal
from app.models import *
from app.api.auth import router as auth_router
from app.api.company import router as company_router
from app.api.partners import router as partners_router

app = FastAPI(title="AA-hub Backend")
app.include_router(auth_router)
app.include_router(company_router)
app.include_router(partners_router)

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