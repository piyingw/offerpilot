from fastapi import APIRouter
from redis import Redis
from sqlalchemy import text

from app.core.config import settings
from app.db.session import engine

router = APIRouter(tags=["健康检查"])


@router.get("/health", summary="健康检查（数据库 / Redis 连通性）")
def health() -> dict[str, str]:
    database = "up"
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        database = "down"

    redis_status = "up"
    client = Redis.from_url(settings.REDIS_URL, socket_connect_timeout=1)
    try:
        client.ping()
    except Exception:
        redis_status = "down"
    finally:
        client.close()

    return {"status": "ok", "database": database, "redis": redis_status}
