from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.security import (
    TIMING_EQUALIZER_HASH,
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_token,
    utcnow_naive,
    verify_password,
)
from app.db.session import get_db
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    TokenOut,
    UserOut,
)

router = APIRouter(prefix="/auth", tags=["认证"])


def _issue_refresh_token(db: Session, user: User) -> str:
    """签发一条新的 refresh token（明文只出现一次，库里只存摘要）。"""
    raw = generate_refresh_token()
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_token(raw),
            expires_at=utcnow_naive() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
    )
    return raw


def _load_valid_refresh(db: Session, raw: str) -> RefreshToken:
    row = (
        db.query(RefreshToken)
        .filter(RefreshToken.token_hash == hash_token(raw))
        .first()
    )
    if row is None or row.revoked_at is not None or row.expires_at < utcnow_naive():
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "登录已过期，请重新登录")
    return row


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

    refresh_raw = _issue_refresh_token(db, user)
    db.commit()
    return TokenOut(
        access_token=create_access_token(user.username),
        refresh_token=refresh_raw,
        user=UserOut.model_validate(user),
    )


@router.post("/refresh", response_model=TokenOut, summary="刷新访问令牌（旋转式，旧令牌立即作废）")
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> TokenOut:
    row = _load_valid_refresh(db, payload.refresh_token)
    user = db.query(User).filter(User.id == row.user_id).first()
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "用户不存在")

    row.revoked_at = utcnow_naive()  # 旋转：旧 refresh token 用一次即作废
    refresh_raw = _issue_refresh_token(db, user)
    db.commit()
    return TokenOut(
        access_token=create_access_token(user.username),
        refresh_token=refresh_raw,
        user=UserOut.model_validate(user),
    )


@router.post(
    "/logout", status_code=status.HTTP_204_NO_CONTENT, summary="登出（吊销 refresh token）"
)
def logout(payload: LogoutRequest, db: Session = Depends(get_db)) -> None:
    row = (
        db.query(RefreshToken)
        .filter(RefreshToken.token_hash == hash_token(payload.refresh_token))
        .first()
    )
    if row is not None and row.revoked_at is None:
        row.revoked_at = utcnow_naive()
        db.commit()


@router.get("/me", response_model=UserOut, summary="当前登录用户")
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
