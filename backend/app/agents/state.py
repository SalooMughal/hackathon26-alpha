from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.plan import SummaryPlan
from app.schemas.sanitized import SanitizedUpdates
from app.schemas.summary import StandupSummary
from app.schemas.validation import ValidationResult


class GraphState(BaseModel):
    """LangGraph state schema — nodes return partial dict updates."""

    standup_date: str
    raw_updates: list[dict]
    sanitized_updates: SanitizedUpdates | None = None
    plan: SummaryPlan | None = None
    raw_summary_output: str | None = None
    parsed_summary: StandupSummary | None = None
    validation: ValidationResult | None = None
    feedback: str | None = None
    revision_count: int = 0
    status: Literal["in_progress", "validated", "degraded"] = "in_progress"
    error: str | None = None
    usage: dict = Field(default_factory=dict)
