from __future__ import annotations
from pydantic import BaseModel


class ProfileSchema(BaseModel):
    name: str
    title: str
    years_of_experience: int
    skills: list[str]
    preferred_roles: list[str]
    preferred_industries: list[str]
    excluded_keywords: list[str]
    min_salary: int | None = None
    work_type: list[str]
    summary: str
