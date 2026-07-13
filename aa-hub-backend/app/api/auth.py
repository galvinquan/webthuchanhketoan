from fastapi import APIRouter, Depends, HTTPException, Response, Request
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models import User
from app.schemas.auth import RegisterRequest, LoginRequest, UserOut
from app.core.security import hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/register", response_model=UserOut)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == payload.username).first()
    if existing:
        raise HTTPException(400, "Username đã tồn tại")
    user = User(
        username=payload.username,
        password=hash_password(payload.password),
        role=payload.role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.post("/login", response_model=UserOut)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or not verify_password(payload.password, user.password):
        raise HTTPException(401, "Sai username hoặc mật khẩu")
    response.set_cookie(key="user_id", value=str(user.id), httponly=True)
    return user

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("user_id")
    return {"message": "Đã đăng xuất"}

@router.get("/me", response_model=UserOut)
def me(request: Request, db: Session = Depends(get_db)):
    user_id = request.cookies.get("user_id")
    if not user_id:
        raise HTTPException(401, "Chưa đăng nhập")
    user = db.get(User, int(user_id))
    if not user:
        raise HTTPException(401, "User không tồn tại")
    return user