from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models import Account, OpeningBalance, Company
from app.schemas.account import AccountOut, OpeningBalanceUpdate, OpeningBalanceOut

router = APIRouter(prefix="/api/accounts", tags=["accounts"])

def get_company_id(request: Request, db: Session = Depends(get_db)):
    user_id = request.cookies.get("user_id")
    if not user_id:
        raise HTTPException(401, "Chưa đăng nhập")
    company = db.query(Company).filter(Company.user_id == int(user_id)).first()
    if not company:
        raise HTTPException(404, "Chưa có thông tin doanh nghiệp")
    return company.id

@router.get("", response_model=list[AccountOut])
def list_accounts(db: Session = Depends(get_db)):
    return db.query(Account).order_by(Account.number).all()

@router.get("/opening-balances", response_model=list[OpeningBalanceOut])
def get_opening_balances(
    company_id: int = Depends(get_company_id),
    db: Session = Depends(get_db)
):
    rows = db.query(OpeningBalance).filter(
        OpeningBalance.company_id == company_id
    ).all()
    return rows

@router.post("/opening-balances")
def save_opening_balances(
    payload: list[OpeningBalanceUpdate],
    company_id: int = Depends(get_company_id),
    db: Session = Depends(get_db)
):
    for item in payload:
        partner_key = item.partner_id
        existing = db.query(OpeningBalance).filter(
            OpeningBalance.company_id == company_id,
            OpeningBalance.account_number == item.account_number,
            OpeningBalance.partner_id == partner_key
        ).first()
        if existing:
            existing.debit = item.debit
            existing.credit = item.credit
        else:
            db.add(OpeningBalance(
                company_id=company_id,
                account_number=item.account_number,
                partner_id=partner_key,
                debit=item.debit,
                credit=item.credit
            ))
    db.commit()
    return {"message": "Đã lưu số dư đầu kỳ"}