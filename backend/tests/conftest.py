import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.db.base import Base
from app.db.session import get_db, get_sessionmaker
from app.main import app
from tests.test_auth import FAKE_USER

FAKE_REPORT = {
    "total_score": 82,
    "dimensions": {"表达清晰": 85, "技术深度": 80, "知识广度": 78, "回答正确性": 85},
    "summary": "整体表现良好，项目描述具体，技术深度有提升空间。",
    "strengths": ["项目描述有条理", "能主动量化结果"],
    "weaknesses": ["技术选型理由阐述不足"],
    "suggestions": ["准备 STAR 法则的项目故事"],
    "question_reviews": [
        {
            "question": "请介绍一下你最有挑战的一个项目。",
            "answer_summary": "商城项目",
            "comment": "整体清晰",
            "score": 82,
        }
    ],
}


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_sessionmaker] = lambda: TestingSession
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def fake_llm(monkeypatch, tmp_path):
    """把所有 LLM 调用替换为确定性的假实现，隔离外部 API。"""
    from app.services import interviewer, resume_parser

    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.setattr(
        resume_parser,
        "structure_resume",
        lambda text: {"basic_info": {"name": "张三"}, "skills": ["Python"]},
    )
    monkeypatch.setattr(
        interviewer,
        "generate_first_question",
        lambda *args, **kwargs: "请介绍一下你最有挑战的一个项目。",
    )

    def fake_stream(*args, **kwargs):
        yield "好的，追问："
        yield "这个项目的日活是多少？"

    monkeypatch.setattr(interviewer, "stream_next_reply", fake_stream)
    monkeypatch.setattr(interviewer, "generate_report", lambda *args, **kwargs: FAKE_REPORT)


@pytest.fixture()
def auth_headers(client):
    client.post("/api/auth/register", json=FAKE_USER)
    creds = {"username": FAKE_USER["username"], "password": FAKE_USER["password"]}
    resp = client.post("/api/auth/login", json=creds)
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}
