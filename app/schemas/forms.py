from datetime import date
from typing import Any, List, Optional

from pydantic import BaseModel, Field


class FormUsageFilters(BaseModel):
    form_id: Optional[int] = None
    requester_id: Optional[int] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    include_answers: bool = True


class FormFieldAnswer(BaseModel):
    question_id: Optional[int] = None
    question: Optional[str] = None
    field_type: Optional[str] = None
    answer: Any = None


class FormUsageRecord(BaseModel):
    answer_id: int
    form_id: Optional[int] = None
    form_name: Optional[str] = None
    requester_id: Optional[int] = None
    requester_name: Optional[str] = None
    used_at: Optional[str] = None
    status: Optional[int] = None
    answers: List[FormFieldAnswer] = Field(default_factory=list)


class FormUsageResponse(BaseModel):
    ok: bool
    count: int
    filters: FormUsageFilters
    submissions: List[FormUsageRecord]
