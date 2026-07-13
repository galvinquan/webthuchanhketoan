from pydantic import BaseModel

class RegisterRequest(BaseModel):
    username: str
    password: str
    role: str = "student"

class LoginRequest(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    id: int
    username: str
    role: str

    class Config:
        from_attributes = True