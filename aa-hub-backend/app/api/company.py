from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models import Company
from app.schemas.company import CompanyCreate, CompanyOut

router = APIRouter(prefix="/api/company", tags=["company"])

def get_current_user_id(request: Request):
    user_id = request.cookies.get("user_id")
    if not user_id:
        raise HTTPException(401, "Chưa đăng nhập")
    return int(user_id)

@router.get("", response_model=CompanyOut)
def get_company(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.user_id == user_id).first()
    if not company:
        raise HTTPException(404, "Chưa có thông tin doanh nghiệp")
    return company

@router.post("", response_model=CompanyOut)
def create_company(payload: CompanyCreate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    existing = db.query(Company).filter(Company.user_id == user_id).first()
    if existing:
        raise HTTPException(400, "Đã có thông tin doanh nghiệp, dùng PUT để cập nhật")
    company = Company(user_id=user_id, **payload.model_dump())
    db.add(company)
    db.commit()
    db.refresh(company)
    return company

@router.put("", response_model=CompanyOut)
def update_company(payload: CompanyCreate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.user_id == user_id).first()
    if not company:
        raise HTTPException(404, "Chưa có thông tin doanh nghiệp")
    for k, v in payload.model_dump().items():
        setattr(company, k, v)
    db.commit()
    db.refresh(company)
    return company