from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import Company, Enrollment, Assignment
from app.schemas.company import CompanyCreate, CompanyUpdate, CompanyOut

router = APIRouter(prefix="/api/company", tags=["company"])


def get_current_user_id(request: Request):
    user_id = request.cookies.get("user_id")
    if not user_id:
        raise HTTPException(401, "Chưa đăng nhập")
    return int(user_id)


def _check_enrolled_in_assignment_class(db: Session, user_id: int, assignment_id: int) -> Assignment:
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(404, "Không tìm thấy bài tập")

    enrollment = (
        db.query(Enrollment)
        .filter(
            Enrollment.class_id == assignment.class_id,
            Enrollment.user_id == user_id,
            Enrollment.status == "active",
        )
        .first()
    )
    if not enrollment:
        raise HTTPException(403, "Bạn chưa tham gia lớp chứa bài tập này")
    return assignment


@router.get("", response_model=CompanyOut)
def get_company(assignment_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    company = (
        db.query(Company)
        .filter(Company.user_id == user_id, Company.assignment_id == assignment_id)
        .first()
    )
    if not company:
        raise HTTPException(404, "Chưa có bài làm cho bài tập này")
    return company


@router.post("", response_model=CompanyOut)
def create_company(payload: CompanyCreate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    _check_enrolled_in_assignment_class(db, user_id, payload.assignment_id)

    existing = (
        db.query(Company)
        .filter(Company.user_id == user_id, Company.assignment_id == payload.assignment_id)
        .first()
    )
    if existing:
        raise HTTPException(400, "Đã có bài làm cho bài tập này, dùng PUT để cập nhật")

    company = Company(user_id=user_id, status="in_progress", **payload.model_dump())
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@router.put("", response_model=CompanyOut)
def update_company(
    assignment_id: int,
    payload: CompanyUpdate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    company = (
        db.query(Company)
        .filter(Company.user_id == user_id, Company.assignment_id == assignment_id)
        .first()
    )
    if not company:
        raise HTTPException(404, "Chưa có bài làm cho bài tập này")
    if company.status == "graded":
        raise HTTPException(400, "Bài đã được chấm điểm, không thể sửa")

    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(company, k, v)
    db.commit()
    db.refresh(company)
    return company


@router.post("/submit", response_model=CompanyOut)
def submit_company(
    assignment_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """SV xác nhận nộp bài: chuyển trạng thái in_progress -> submitted."""
    company = (
        db.query(Company)
        .filter(Company.user_id == user_id, Company.assignment_id == assignment_id)
        .first()
    )
    if not company:
        raise HTTPException(404, "Chưa có bài làm cho bài tập này")
    if company.status == "graded":
        raise HTTPException(400, "Bài đã được chấm điểm")

    company.status = "submitted"
    db.commit()
    db.refresh(company)
    return company
