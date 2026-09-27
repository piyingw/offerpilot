import json
from datetime import datetime

from pydantic import BaseModel, model_validator

from app.models.resume import Resume


class ResumeOut(BaseModel):
    id: int
    filename: str
    parse_status: str
    created_at: datetime
    content: dict | None = None

    @model_validator(mode="before")
    @classmethod
    def _extract_content(cls, data: object) -> object:
        if isinstance(data, Resume):
            try:
                parsed = json.loads(data.content_json) if data.content_json else None
            except json.JSONDecodeError:
                parsed = None
            return {
                "id": data.id,
                "filename": data.filename,
                "parse_status": data.parse_status,
                "created_at": data.created_at,
                "content": parsed,
            }
        return data
