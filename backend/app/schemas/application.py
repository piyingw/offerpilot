from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

StatusLiteral = Literal[
    "applied",
    "viewed",
    "written_test",
    "interview_1",
    "interview_2",
    "interview_3",
    "hr_interview",
    "offer",
    "rejected",
    "closed",
]

ChannelLiteral = Literal[
    "boss", "zhilian", "51job", "liepin", "niuke", "official", "referral", "other"
]


class ApplicationCreate(BaseModel):
    company: str = Field(min_length=1, max_length=120)
    position: str = Field(min_length=1, max_length=120)
    channel: ChannelLiteral = "other"
    current_status: StatusLiteral = "applied"
    salary: str | None = Field(default=None, max_length=60)
    jd_url: str | None = Field(default=None, max_length=512)
    note: str | None = None
    resume_id: int | None = None
    applied_at: datetime | None = None


class ApplicationUpdate(BaseModel):
    company: str | None = Field(default=None, min_length=1, max_length=120)
    position: str | None = Field(default=None, min_length=1, max_length=120)
    channel: ChannelLiteral | None = None
    salary: str | None = Field(default=None, max_length=60)
    jd_url: str | None = Field(default=None, max_length=512)
    note: str | None = None
    resume_id: int | None = None
    # 状态变更专用：仅当 status 与当前不同时生效
    status: StatusLiteral | None = None
    status_changed_at: datetime | None = None
    status_note: str | None = Field(default=None, max_length=255)


class EventOut(BaseModel):
    id: int
    from_status: str | None
    to_status: str
    happened_at: datetime
    note: str | None

    model_config = {"from_attributes": True}


class ApplicationOut(BaseModel):
    id: int
    company: str
    position: str
    channel: str
    current_status: str
    salary: str | None
    jd_url: str | None
    note: str | None
    resume_id: int | None
    applied_at: datetime
    created_at: datetime
    updated_at: datetime
    events: list[EventOut] = []

    model_config = {"from_attributes": True}


class ApplicationItemOut(BaseModel):
    """列表页使用的精简结构。"""

    id: int
    company: str
    position: str
    channel: str
    current_status: str
    salary: str | None
    applied_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ApplicationPageOut(BaseModel):
    items: list[ApplicationItemOut]
    total: int
    page: int
    page_size: int


class FunnelItem(BaseModel):
    status: str
    label: str
    count: int


class StatusCount(BaseModel):
    status: str
    label: str
    count: int


class WeekCount(BaseModel):
    week: str
    count: int


class RecentEventItem(BaseModel):
    id: int
    company: str
    position: str
    from_status: str | None
    to_status: str
    happened_at: datetime
    note: str | None


class StatsOut(BaseModel):
    total: int
    active: int
    offers: int
    rejected: int
    funnel: list[FunnelItem]
    distribution: list[StatusCount]
    weekly: list[WeekCount]
    recent_events: list[RecentEventItem]
