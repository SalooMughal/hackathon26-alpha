from typing import Literal

from pydantic import BaseModel, Field


class SummaryPlan(BaseModel):
    """Structured plan produced by the planner agent."""

    grouping: Literal["by_section", "by_person"]
    section_order: list[str]
    emphasis: list[str]
    cross_link_hints: list[str] = Field(default_factory=list)
    tone: Literal["neutral", "urgent"]
    length_budget_words: int = Field(ge=80, le=220)
