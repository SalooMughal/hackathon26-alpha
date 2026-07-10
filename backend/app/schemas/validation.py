from pydantic import BaseModel, Field, field_validator


class ValidationResult(BaseModel):
    """Structured validation output from the validator agent."""

    approved: bool
    issues: list[str] = Field(default_factory=list)

    @field_validator("issues")
    @classmethod
    def _max_five_issues(cls, v: list[str]) -> list[str]:
        return v[:5]
