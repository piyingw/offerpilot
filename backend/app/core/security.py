import hashlib
import secrets
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from app.core.config import settings

# 校验一次即丢弃的哈希，用于登录时抹平"用户不存在"与"密码错误"的耗时差
TIMING_EQUALIZER_HASH = bcrypt.hashpw(b"timing-equalizer-dummy", bcrypt.gensalt(rounds=10)).decode()


def utcnow_naive() -> datetime:
    """数据库 DateTime 列统一存朴素 UTC 时间，避免时区混用。"""
    return datetime.now(UTC).replace(tzinfo=None)


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    """refresh token 只存 SHA-256 摘要，库被拖走也无法直接使用。"""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def create_access_token(subject: str) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> str | None:
    """返回 token 中的 sub（用户名），无效或过期返回 None。"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except jwt.PyJWTError:
        return None
    sub = payload.get("sub")
    return str(sub) if sub is not None else None
