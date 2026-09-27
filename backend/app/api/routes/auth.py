from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import (
    TIMING_EQUALIZER_HASH,
    create_access_token,
    hash_password,
    verify_password,
)
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenOut, UserOut

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post(
    "/register", response_model=UserOut, status_code=status.HTTP_201_CREATED, summary="注册"
)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> User:
    exists = (
        db.query(User)
        .filter((User.username == payload.username) | (User.email == payload.email))
        .first()
    )
    if exists:
        raise HTTPException(status.HTTP_409_CONFLICT, "用户名或邮箱已被注册")
    user = User(
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        # 并发注册撞唯一约束：检查-插入之间存在竞态，唯一索引兜底
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "用户名或邮箱已被注册") from None
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenOut, summary="登录（用户名或邮箱）")
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenOut:
    user = (
        db.query(User)
        .filter((User.username == payload.username) | (User.email == payload.username))
        .first()
    )
    if user is None:
        # 对不存在的用户也执行一次哈希校验，避免响应时间差暴露用户是否注册过
        verify_password(payload.password, TIMING_EQUALIZER_HASH)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "用户名或密码错误")
    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "用户名或密码错误")
    return TokenOut(
        access_token=create_access_token(user.username), user=UserOut.model_validate(user)
    )


@router.get("/me", response_model=UserOut, summary="当前登录用户")
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
