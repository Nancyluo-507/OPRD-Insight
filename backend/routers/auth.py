from fastapi import APIRouter, Header
from pydantic import BaseModel
from database.session import SessionLocal
from database.models import User
from database.crud import get_user, get_user_by_name, create_user
from utils.helpers import row_to_dict, hash_password, verify_password, create_token, verify_token
from utils.exceptions import AppException

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class RegisterBody(BaseModel):
    name: str
    password: str
    email: str = ""


class LoginBody(BaseModel):
    name: str
    password: str


def _get_current_user(authorization: str | None) -> dict | None:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    uid = verify_token(authorization[7:])
    if not uid:
        return None
    return get_user(uid)


@router.post("/register")
def register(body: RegisterBody):
    if get_user_by_name(body.name):
        raise AppException("Username already exists", 409)
    user = create_user(body.name, hash_password(body.password), body.email)
    auth_token = create_token(user.id)
    return {"user": row_to_dict(user, exclude=["password_hash"]), "token": auth_token}


@router.post("/login")
def login(body: LoginBody):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.name == body.name).first()
    finally:
        db.close()
    if not user or not verify_password(body.password, user.password_hash):
        raise AppException("Invalid credentials", 401)
    return {"user": row_to_dict(user, exclude=["password_hash"]), "token": create_token(user.id)}


@router.get("/me")
def auth_me(authorization: str = Header(None)):
    user = _get_current_user(authorization) if authorization else None
    if not user:
        raise AppException("Unauthorized", 401)
    return {"user": user}



