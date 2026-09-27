from collections import Counter
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.status import STAGE_ORDER, STATUS_LABELS
from app.db.session import get_db
from app.models.application import Application, ApplicationEvent
from app.models.resume import Resume
from app.models.user import User
from app.schemas.application import (
    ApplicationCreate,
    ApplicationItemOut,
    ApplicationOut,
    ApplicationUpdate,
    FunnelItem,
    RecentEventItem,
    StatsOut,
    StatusCount,
    WeekCount,
)

router = APIRouter(prefix="/applications", tags=["投递记录"])


def _owned_application(db: Session, user: User, application_id: int) -> Application:
    application = (
        db.query(Application)
        .filter(Application.id == application_id, Application.user_id == user.id)
        .first()
    )
    if application is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "投递记录不存在")
    return application


def _validate_resume(db: Session, user: User, resume_id: int) -> None:
    if (
        db.query(Resume)
        .filter(Resume.id == resume_id, Resume.user_id == user.id)
        .first()
        is None
    ):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "所选简历不存在")


@router.post(
    "", response_model=ApplicationOut, status_code=status.HTTP_201_CREATED, summary="新增投递记录"
)
def create_application(
    payload: ApplicationCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Application:
    if payload.resume_id is not None:
        _validate_resume(db, user, payload.resume_id)
    applied_at = payload.applied_at or datetime.now()
    application = Application(
        user_id=user.id,
        resume_id=payload.resume_id,
        company=payload.company,
        position=payload.position,
        channel=payload.channel,
        jd_url=payload.jd_url,
        salary=payload.salary,
        note=payload.note,
        current_status=payload.current_status,
        applied_at=applied_at,
    )
    application.events.append(
        ApplicationEvent(from_status=None, to_status=payload.current_status, happened_at=applied_at)
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


@router.get("", response_model=list[ApplicationItemOut], summary="投递记录列表")
def list_applications(
    q: str | None = None,
    status_filter: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Application]:
    query = db.query(Application).filter(Application.user_id == user.id)
    if status_filter:
        query = query.filter(Application.current_status.in_(status_filter.split(",")))
    if q:
        like = f"%{q}%"
        query = query.filter(Application.company.like(like) | Application.position.like(like))
    return query.order_by(Application.applied_at.desc(), Application.id.desc()).all()


@router.get("/stats", response_model=StatsOut, summary="看板统计（漏斗 / 分布 / 周投递量）")
def application_stats(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> StatsOut:
    applications = (
        db.query(Application).filter(Application.user_id == user.id).all()
    )
    total = len(applications)
    dist = Counter(a.current_status for a in applications)

    # 漏斗口径：累计"曾到达该阶段"的投递数（回退/被拒不影响已到达的深度）
    stage_index = {s: i for i, s in enumerate(STAGE_ORDER)}
    reached: list[int] = []
    for application in applications:
        idxs = [
            stage_index[e.to_status]
            for e in application.events
            if e.to_status in stage_index
        ]
        if application.current_status in stage_index:
            idxs.append(stage_index[application.current_status])
        reached.append(max(idxs) if idxs else 0)  # 每条记录至少到达"已投递"

    funnel = [
        FunnelItem(status=s, label=STATUS_LABELS[s], count=sum(1 for r in reached if r >= i))
        for i, s in enumerate(STAGE_ORDER)
    ]
    distribution = [
        StatusCount(status=s, label=STATUS_LABELS[s], count=dist.get(s, 0)) for s in STATUS_LABELS
    ]

    today = date.today()
    monday = today - timedelta(days=today.weekday())
    weekly = []
    for offset in range(7, -1, -1):
        week_start = monday - timedelta(weeks=offset)
        count = sum(
            1
            for a in applications
            if week_start <= a.applied_at.date() < week_start + timedelta(days=7)
        )
        weekly.append(WeekCount(week=week_start.strftime("%m-%d"), count=count))

    recent = (
        db.query(ApplicationEvent)
        .join(Application, ApplicationEvent.application_id == Application.id)
        .filter(Application.user_id == user.id)
        .order_by(ApplicationEvent.happened_at.desc(), ApplicationEvent.id.desc())
        .limit(10)
        .all()
    )
    recent_events = [
        RecentEventItem(
            id=e.id,
            company=e.application.company,
            position=e.application.position,
            from_status=e.from_status,
            to_status=e.to_status,
            happened_at=e.happened_at,
            note=e.note,
        )
        for e in recent
    ]

    active_statuses = set(STATUS_LABELS) - {"offer", "rejected", "closed"}
    return StatsOut(
        total=total,
        active=sum(1 for a in applications if a.current_status in active_statuses),
        offers=dist.get("offer", 0),
        rejected=dist.get("rejected", 0) + dist.get("closed", 0),
        funnel=funnel,
        distribution=distribution,
        weekly=weekly,
        recent_events=recent_events,
    )


@router.get("/{application_id}", response_model=ApplicationOut, summary="投递详情（含状态时间线）")
def get_application(
    application_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> Application:
    return _owned_application(db, user, application_id)


@router.patch("/{application_id}", response_model=ApplicationOut, summary="更新投递记录 / 状态流转")
def update_application(
    application_id: int,
    payload: ApplicationUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Application:
    application = _owned_application(db, user, application_id)
    data = payload.model_dump(exclude_unset=True)

    new_status = data.pop("status", None)
    changed_at = data.pop("status_changed_at", None)
    status_note = data.pop("status_note", None)

    if "resume_id" in data and data["resume_id"] is not None:
        _validate_resume(db, user, data["resume_id"])
    for key, value in data.items():
        setattr(application, key, value)

    if new_status and new_status != application.current_status:
        application.events.append(
            ApplicationEvent(
                from_status=application.current_status,
                to_status=new_status,
                happened_at=changed_at or datetime.now(),
                note=status_note,
            )
        )
        application.current_status = new_status

    db.commit()
    db.refresh(application)
    return application


@router.delete(
    "/{application_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除投递记录"
)
def delete_application(
    application_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> None:
    application = _owned_application(db, user, application_id)
    db.delete(application)
    db.commit()
