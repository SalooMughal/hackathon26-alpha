from datetime import date

from app.agents.prompts.loader import load_prompt
from app.schemas.sanitized import SanitizedMember


def test_prompt_loader_parses_sections():
    parts = load_prompt("summarizer_v1")
    assert parts.system
    assert parts.human_template
    assert parts.feedback_template
    assert "{" in parts.system
    assert "{standup_date}" in parts.human_template


def test_summarizer_system_survives_unformatted():
    parts = load_prompt("summarizer_v1")
    assert "{" in parts.system
    assert parts.system.count("{") >= 2


def test_human_template_formats_without_keyerror():
    parts = load_prompt("planner_v1")
    formatted = parts.human_template.format(
        standup_date="2026-07-10",
        team_updates="<member>test</member>",
    )
    assert "2026-07-10" in formatted


def test_format_team_updates_from_sanitized():
    from app.agents.prompts.loader import format_team_updates

    text = format_team_updates(
        [
            SanitizedMember(
                name="Sabir",
                yesterday="Built API",
                today="Tests",
                blockers="",
                was_modified=False,
            )
        ]
    )
    assert 'name="Sabir"' in text
    assert "blockers: none stated" in text
