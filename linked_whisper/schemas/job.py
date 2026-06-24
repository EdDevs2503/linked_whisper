from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel


class JobPosition(BaseModel):
    id: str
    source: str
    title: str
    company: str
    description: str
    tags: list[str]
    location: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    url: str
    posted_at: datetime | None = None
