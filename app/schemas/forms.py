from datetime import date
from typing import List, Optional

from pydantic import BaseModel


class FormUsageFilters(BaseModel):
    form_id: Optional[int] = None
    requester_id: Optional[int] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None


class FormUsageRecord(BaseModel):
    answer_id: int
    form_id: Optional[int] = None
    form_name: Optional[str] = None
    requester_id: Optional[int] = None
    requester_name: Optional[str] = None
    used_at: Optional[str] = None
    status: Optional[int] = None


class FormUsageResponse(BaseModel):
    ok: bool
    count: int
    filters: FormUsageFilters
    submissions: List[FormUsageRecord]

