from pydantic import BaseModel, Field


class ValidationResult(BaseModel):
    """Structured validation output from the validator agent (Phase 2)."""

    approved: bool
    issues: list[str] = Field(default_factory=list)
