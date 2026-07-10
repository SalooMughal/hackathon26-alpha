from enum import Enum

from pydantic import BaseModel, Field


class MemberFlag(str, Enum):
    """Categories flagged during input sanitization."""

    sexual_content = "sexual_content"
    harassment_or_abuse = "harassment_or_abuse"
    hate_speech = "hate_speech"
    violence_threat = "violence_threat"
    profanity = "profanity"
    prompt_injection = "prompt_injection"
    credentials_or_pii = "credentials_or_pii"
    spam_or_off_topic = "spam_or_off_topic"


class SanitizedMember(BaseModel):
    """One member's cleaned standup fields after sanitization."""

    name: str
    yesterday: str
    today: str
    blockers: str
    was_modified: bool
    flags: list[MemberFlag] = Field(default_factory=list)
    fully_redacted: bool = False


class SanitizedUpdates(BaseModel):
    """Full team output from the sanitizer agent."""

    members: list[SanitizedMember]
    notes: list[str] = Field(default_factory=list)
