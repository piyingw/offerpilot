import json
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.models.interview import InterviewReport


class InterviewCreate(BaseModel):
    resume_id: int
    interview_type: Literal["resume", "technical"]
    difficulty: Literal["easy", "medium", "hard"] = "medium"
    position_name: str | None = Field(default=None, max_length=120)
    jd_text: str | None = Field(default=None, max_length=8000)


class AnswerPayload(BaseModel):
    content: str = Field(min_length=1, max_length=4000)


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ReportOut(BaseModel):
    id: int
    total_score: int | None = None
    dimensions: dict | None = None
    summary: str | None = None
    strengths: list[str] = []
    weaknesses: list[str] = []
    suggestions: list[str] = []
    question_reviews: list[dict] = []
    created_at: datetime

    @model_validator(mode="before")
    @classmethod
    def _extract_json_columns(cls, data: object) -> object:
        if isinstance(data, InterviewReport):

            def loads(raw: str | None) -> object:
                try:
                    return json.loads(raw) if raw else None
                except json.JSONDecodeError:
                    return None

            strengths = loads(data.strengths_json)
            weaknesses = loads(data.weaknesses_json)
            suggestions = loads(data.suggestions_json)
            return {
                "id": data.id,
                "total_score": data.total_score,
                "dimensions": loads(data.dimensions_json),
                "summary": data.summary,
                "strengths": strengths if isinstance(strengths, list) else [],
                "weaknesses": weaknesses if isinstance(weaknesses, list) else [],
                "suggestions": suggestions if isinstance(suggestions, list) else [],
                "question_reviews": loads(data.questions_json) or [],
                "created_at": data.created_at,
            }
        return data


class SessionOut(BaseModel):
    id: int
    resume_id: int | None
    interview_type: str
    difficulty: str
    position_name: str | None
    jd_text: str | None
    status: str
    started_at: datetime
    ended_at: datetime | None
    total_score: int | None
    messages: list[MessageOut] = []
    report: ReportOut | None = None

    model_config = {"from_attributes": True}


class SessionItemOut(BaseModel):
    """列表页使用的精简结构。"""

    id: int
    interview_type: str
    difficulty: str
    position_name: str | None
    status: str
    total_score: int | None
    started_at: datetime
    ended_at: datetime | None

    model_config = {"from_attributes": True}
