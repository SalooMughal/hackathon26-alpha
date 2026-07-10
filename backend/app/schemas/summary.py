import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PersonItems(BaseModel):
    person: str
    items: list[str]


class BlockerItem(BaseModel):
    person: str
    item: str
    severity: Literal["low", "medium", "high"] = "low"


class StandupSummary(BaseModel):
    tldr: str
    done: list[PersonItems]
    doing: list[PersonItems]
    blockers: list[BlockerItem]
    cross_links: list[str] = Field(default_factory=list)


class SummaryCreateRequest(BaseModel):
    standup_date: date | None = None


class SummaryResponse(BaseModel):
    summary_id: uuid.UUID
    status: Literal["validated", "degraded"]
    content: StandupSummary
    rendered_markdown: str
    model_meta: dict


class SummaryDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    standup_date: date
    status: Literal["validated", "degraded"]
    content: StandupSummary
    rendered_markdown: str
    model_meta: dict
    prompt_version: str
    created_at: datetime


def render_markdown(summary: StandupSummary, standup_date: date | None = None) -> str:
    """Deterministic Slack-flavored markdown renderer (no LLM)."""
    header_date = standup_date.isoformat() if standup_date else "Today"
    lines = [f"📋 Daily Standup — {header_date}", "", summary.tldr, ""]

    lines.extend(["✅ Done (Yesterday)", ""])
    for section in summary.done:
        items = "; ".join(section.items)
        lines.append(f"• {section.person}: {items}")
    lines.append("")

    lines.extend(["🔄 Doing (Today)", ""])
    for section in summary.doing:
        items = "; ".join(section.items)
        lines.append(f"• {section.person}: {items}")
    lines.append("")

    lines.extend(["🚧 Blockers", ""])
    if summary.blockers:
        for blocker in summary.blockers:
            lines.append(f"• {blocker.person}: {blocker.item}")
    else:
        lines.append("• None")
    lines.append("")

    if summary.cross_links:
        lines.extend(["🔗 Cross-links", ""])
        for link in summary.cross_links:
            lines.append(f"• {link}")

    return "\n".join(lines)
