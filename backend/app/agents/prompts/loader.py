import re
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel

from app.schemas.sanitized import SanitizedMember

PROMPTS_DIR = Path(__file__).resolve().parent
SECTION_HEADER = re.compile(r"^## (.+)$", re.MULTILINE)


class PromptParts(BaseModel):
    system: str
    human_template: str
    feedback_template: str | None = None


def _strip_comment_header(text: str) -> str:
    lines = text.splitlines()
    body_start = 0
    for i, line in enumerate(lines):
        if line.startswith("## "):
            body_start = i
            break
    return "\n".join(lines[body_start:])


def _parse_sections(text: str) -> dict[str, str]:
    cleaned = _strip_comment_header(text)
    matches = list(SECTION_HEADER.finditer(cleaned))
    sections: dict[str, str] = {}
    for idx, match in enumerate(matches):
        name = match.group(1).strip().upper()
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(cleaned)
        sections[name] = cleaned[start:end].strip()
    return sections


@lru_cache
def load_prompt(name: str) -> PromptParts:
    path = PROMPTS_DIR / f"{name}.txt"
    raw = path.read_text(encoding="utf-8")
    sections = _parse_sections(raw)
    system = sections.get("SYSTEM MESSAGE", "")
    human = sections.get("HUMAN MESSAGE TEMPLATE", "")
    feedback = sections.get("FEEDBACK BLOCK TEMPLATE (ONLY APPENDED ON REVISION PASSES)")
    if feedback is None:
        feedback = sections.get("FEEDBACK BLOCK TEMPLATE")
    return PromptParts(
        system=system,
        human_template=human,
        feedback_template=feedback,
    )


def format_team_updates(members: list[SanitizedMember] | list[dict]) -> str:
    """Format member updates as XML blocks for prompt templates."""
    blocks: list[str] = []
    for member in members:
        if isinstance(member, SanitizedMember):
            name = member.name
            yesterday = member.yesterday
            today = member.today
            blockers = member.blockers or "none stated"
        else:
            name = member["name"]
            yesterday = member.get("yesterday", "")
            today = member.get("today", "")
            blockers = member.get("blockers") or "none stated"
        blocks.append(
            f'<member name="{name}">\n'
            f"yesterday: {yesterday}\n"
            f"today: {today}\n"
            f"blockers: {blockers}\n"
            f"</member>"
        )
    return "\n".join(blocks)
