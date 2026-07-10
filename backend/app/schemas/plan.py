from pydantic import BaseModel, Field


class SummaryPlan(BaseModel):
    """Structured plan produced by the planner agent (Phase 2)."""

    sections_order: list[str] = Field(
        default_factory=lambda: ["done", "doing", "blockers"]
    )
    grouping_strategy: str = "by_section"
    tone: str = "concise"
    emphasis: list[str] = Field(default_factory=list)
