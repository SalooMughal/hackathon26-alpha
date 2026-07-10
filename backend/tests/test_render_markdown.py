from datetime import date

from app.schemas.summary import Blocker, PersonItems, StandupSummary, render_markdown


def test_render_markdown_golden():
    summary = StandupSummary(
        tldr="API integration on track.",
        done=[PersonItems(person="Sabir", items=["Built routes"])],
        doing=[PersonItems(person="Asad", items=["UI panel"])],
        blockers=[Blocker(person="Sabir", item="Need API key", severity="high")],
        cross_links=["Sabir blocked on key from Shahryar."],
    )
    md = render_markdown(summary, date(2026, 7, 10))
    assert "*Done (Yesterday)*" in md
    assert "*Doing (Today)*" in md
    assert "*Blockers*" in md
    assert "Sabir: Built routes" in md
    assert "⚠ auto-generated without AI validation" not in md


def test_render_markdown_degraded_footer():
    summary = StandupSummary(
        tldr="Fallback summary.",
        done=[],
        doing=[],
        blockers=[],
    )
    md = render_markdown(summary, date(2026, 7, 10), degraded=True)
    assert "⚠ auto-generated without AI validation" in md


def test_render_markdown_missing_members_section():
    summary = StandupSummary(
        tldr="Partial team update.",
        done=[PersonItems(person="Sabir", items=["Built API"])],
        doing=[PersonItems(person="Sabir", items=["Testing"])],
        blockers=[],
    )
    md = render_markdown(summary, date(2026, 7, 10), missing_members=["Asad", "Zaha"])
    assert "*Missing updates*" in md
    assert "Asad: No update submitted for this date" in md
    assert "Zaha: No update submitted for this date" in md
