from app.agent.skills.default_skills import (
    create_default_skill_registry,
)


def test_default_registry_contains_wh_skill():
    registry = (
        create_default_skill_registry()
    )

    skill = registry.resolve(
        "WH_WINDOW"
    )

    assert skill is not None
    assert skill.capability_name == (
        "WH_WINDOW"
    )


def test_default_registry_contains_excel_skill():
    registry = (
        create_default_skill_registry()
    )

    assert registry.supports("EXCEL")


def test_default_registry_contains_word_skill():
    registry = (
        create_default_skill_registry()
    )

    assert registry.supports("WORD")


def test_unknown_skill_returns_none():
    registry = (
        create_default_skill_registry()
    )

    assert registry.resolve(
        "UNKNOWN"
    ) is None
