from app.services.update_quality import validate_update_fields


def test_accepts_detailed_update():
    issues = validate_update_fields(
        yesterday="Implemented POST /api/v1/summary and wired the LangGraph pipeline.",
        today="Testing manual edit and regenerate flows in Postman.",
        blockers="None",
    )
    assert issues == []


def test_rejects_test_test():
    issues = validate_update_fields(
        yesterday="test",
        today="test",
        blockers="None",
    )
    assert len(issues) == 2
    assert all("yesterday" in i or "today" in i for i in issues)


def test_rejects_vague_ui_completed():
    issues = validate_update_fields(
        yesterday="working on ui.",
        today="ui completed.",
        blockers="None",
    )
    assert len(issues) >= 1


def test_accepts_informal_but_specific():
    issues = validate_update_fields(
        yesterday="Fixed the summary regenerate bug and updated Postman docs.",
        today="Pairing with Asad on the frontend summary panel.",
        blockers="None",
    )
    assert issues == []


def test_accepts_short_but_specific_sentence():
    issues = validate_update_fields(
        yesterday="Merged the OAuth login fix into main branch.",
        today="Writing integration tests for the updates API.",
        blockers="None",
    )
    assert issues == []


def test_rejects_leading_garbage_digits():
    issues = validate_update_fields(
        yesterday="Added summary endpoints for the team.",
        today="1111Testing manual edit flows.",
        blockers="None",
    )
    assert any("today" in i for i in issues)
