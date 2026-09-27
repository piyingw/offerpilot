from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    resume_id: Mapped[int | None] = mapped_column(
        ForeignKey("resumes.id", ondelete="SET NULL"), nullable=True
    )
    company: Mapped[str] = mapped_column(String(120), index=True)
    position: Mapped[str] = mapped_column(String(120))
    channel: Mapped[str] = mapped_column(String(30), default="other")
    jd_url: Mapped[str | None] = mapped_column(String(512))
    salary: Mapped[str | None] = mapped_column(String(60))
    note: Mapped[str | None] = mapped_column(Text)
    current_status: Mapped[str] = mapped_column(String(20), default="applied", index=True)
    applied_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    events: Mapped[list["ApplicationEvent"]] = relationship(
        back_populates="application", cascade="all, delete-orphan", order_by="ApplicationEvent.id"
    )


class ApplicationEvent(Base):
    """投递状态流转的时间线；每次状态变化追加一条。"""

    __tablename__ = "application_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    application_id: Mapped[int] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), index=True
    )
    from_status: Mapped[str | None] = mapped_column(String(20))  # 首条事件为 None
    to_status: Mapped[str] = mapped_column(String(20))
    happened_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    note: Mapped[str | None] = mapped_column(String(255))

    application: Mapped["Application"] = relationship(back_populates="events")
