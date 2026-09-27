import json
from collections.abc import Generator
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, sessionmaker

from app.api.deps import get_current_user
from app.db.session import get_db, get_sessionmaker
from app.models.interview import InterviewMessage, InterviewReport, InterviewSession
from app.models.resume import Resume
from app.models.user import User
from app.schemas.interview import (
    AnswerPayload,
    InterviewCreate,
    ReportOut,
    SessionItemOut,
    SessionOut,
)
from app.services import interviewer
from app.services.llm import LLMNotConfiguredError

router = APIRouter(prefix="/interviews", tags=["模拟面试"])


def _owned_session(db: Session, user: User, session_id: int) -> InterviewSession:
    session = (
        db.query(InterviewSession)
        .filter(InterviewSession.id == session_id, InterviewSession.user_id == user.id)
        .first()
    )
    if session is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "面试会话不存在")
    return session


def _history(session: InterviewSession) -> list[dict]:
    return [
        {"role": m.role, "content": m.content}
        for m in session.messages
    ]


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


def _as_int(value: object) -> int | None:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


@router.post("", response_model=SessionOut, status_code=status.HTTP_201_CREATED, summary="创建面试")
def create_interview(
    payload: InterviewCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> InterviewSession:
    resume = (
        db.query(Resume).filter(Resume.id == payload.resume_id, Resume.user_id == user.id).first()
    )
    if resume is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "简历不存在")
    snapshot = resume.content_json or (resume.content_text or "")[:6000]
    if not snapshot.strip():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "该简历没有可用内容，请重新上传")

    try:
        first_question = interviewer.generate_first_question(
            payload.interview_type,
            payload.difficulty,
            snapshot,
            payload.jd_text,
            payload.position_name,
        )
    except LLMNotConfiguredError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from None
    except Exception:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "生成第一题失败，请稍后重试") from None

    session = InterviewSession(
        user_id=user.id,
        resume_id=resume.id,
        interview_type=payload.interview_type,
        difficulty=payload.difficulty,
        position_name=payload.position_name,
        jd_text=payload.jd_text,
        resume_snapshot=snapshot,
        status="in_progress",
    )
    session.messages.append(InterviewMessage(role="interviewer", content=first_question))
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("", response_model=list[SessionItemOut], summary="面试列表")
def list_interviews(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[InterviewSession]:
    return (
        db.query(InterviewSession)
        .filter(InterviewSession.user_id == user.id)
        .order_by(InterviewSession.id.desc())
        .all()
    )


@router.get("/{session_id}", response_model=SessionOut, summary="面试详情（含消息与报告）")
def get_interview(
    session_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> InterviewSession:
    return _owned_session(db, user, session_id)


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除面试记录")
def delete_interview(
    session_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> None:
    session = _owned_session(db, user, session_id)
    db.delete(session)
    db.commit()


@router.post("/{session_id}/answer", summary="回答问题（SSE 流式返回面试官下一条消息）")
def answer(
    session_id: int,
    payload: AnswerPayload,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    session_factory: "sessionmaker[Session]" = Depends(get_sessionmaker),
) -> StreamingResponse:
    session = _owned_session(db, user, session_id)
    if session.status != "in_progress":
        raise HTTPException(status.HTTP_409_CONFLICT, "面试已结束，无法继续回答")
    db.add(InterviewMessage(session_id=session.id, role="candidate", content=payload.content))
    db.commit()
    history = _history(session)

    def event_stream() -> Generator[str]:
        chunks: list[str] = []
        try:
            for delta in interviewer.stream_next_reply(
                session.interview_type,
                session.difficulty,
                session.resume_snapshot or "",
                session.jd_text,
                session.position_name,
                history,
            ):
                chunks.append(delta)
                yield _sse({"delta": delta})
        except LLMNotConfiguredError as exc:
            yield _sse({"error": str(exc)})
            return
        except Exception:
            yield _sse({"error": "生成回复失败，请重试"})
            return

        content = "".join(chunks).strip() or "（面试官暂时没有回应，请重新发送）"
        # 流式响应期间请求级 Session 可能已回收，这里用独立会话持久化
        saved = session_factory()
        try:
            saved.add(InterviewMessage(session_id=session.id, role="interviewer", content=content))
            saved.commit()
        finally:
            saved.close()
        yield _sse({"done": True, "content": content})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/{session_id}/finish", response_model=ReportOut, summary="结束面试并生成评估报告")
def finish_interview(
    session_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> InterviewReport:
    session = _owned_session(db, user, session_id)
    if session.report is not None:
        return session.report  # 幂等：重复调用返回已有报告

    history = _history(session)
    if not any(m["role"] == "candidate" for m in history):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "还没有任何回答，无法生成报告")

    try:
        data = interviewer.generate_report(
            session.interview_type, history, session.resume_snapshot or ""
        )
    except LLMNotConfiguredError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from None
    except ValueError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc)) from None
    except Exception:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "报告生成失败，请稍后重试") from None

    total_score = _as_int(data.get("total_score"))
    report = InterviewReport(
        session_id=session.id,
        total_score=total_score,
        dimensions_json=json.dumps(data.get("dimensions"), ensure_ascii=False)
        if data.get("dimensions")
        else None,
        summary=str(data.get("summary") or ""),
        strengths_json=json.dumps(data.get("strengths") or [], ensure_ascii=False),
        weaknesses_json=json.dumps(data.get("weaknesses") or [], ensure_ascii=False),
        suggestions_json=json.dumps(data.get("suggestions") or [], ensure_ascii=False),
        questions_json=json.dumps(data.get("question_reviews") or [], ensure_ascii=False),
    )
    db.add(report)
    session.status = "finished"
    session.ended_at = datetime.now()
    session.total_score = total_score
    db.commit()
    db.refresh(report)
    return report
