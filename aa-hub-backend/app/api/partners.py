from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models import Partner, Company
from app.schemas.partner import PartnerCreate, PartnerOut

router = APIRouter(prefix="/api/partners", tags=["partners"])

def get_company_id(request: Request, db: Session = Depends(get_db)):
    user_id = request.cookies.get("user_id")
    if not user_id:
        raise HTTPException(401, "Chưa đăng nhập")
    company = db.query(Company).filter(Company.user_id == int(user_id)).first()
    if not company:
        raise HTTPException(404, "Chưa có thông tin doanh nghiệp")
    return company.id

@router.get("", response_model=list[PartnerOut])
def list_partners(type: str = None, company_id: int = Depends(get_company_id), db: Session = Depends(get_db)):
    q = db.query(Partner).filter(Partner.company_id == company_id)
    if type:
        q = q.filter(Partner.type == type)
    return q.all()

@router.post("", response_model=PartnerOut)
def create_partner(payload: PartnerCreate, company_id: int = Depends(get_company_id), db: Session = Depends(get_db)):
    partner = Partner(company_id=company_id, **payload.model_dump())
    db.add(partner)
    db.commit()
    db.refresh(partner)
    return partner

@router.delete("/{partner_id}")
def delete_partner(partner_id: int, company_id: int = Depends(get_company_id), db: Session = Depends(get_db)):
    partner = db.query(Partner).filter(Partner.id == partner_id, Partner.company_id == company_id).first()
    if not partner:
        raise HTTPException(404, "Không tìm thấy")
    db.delete(partner)
    db.commit()
    return {"message": "Đã xóa"}