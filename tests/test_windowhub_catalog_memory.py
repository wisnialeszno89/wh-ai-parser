"""Local catalog skill memory must be explicit, validated and reusable."""
from app.agent.learning.windowhub_catalog_memory import (
    skill_key, read_skill, record_skill,
)


def test_catalog_skill_needs_both_human_approval_and_readback(tmp_path):
    path = tmp_path / "skills.json"
    kind, key = skill_key(outside="Antracyt", inside="Biały")
    assert read_skill(kind, key, path=path) is None
    assert record_skill(
        kind, key, "RAL 701605 / 9016", path=path,
        human_confirmed=False, readback_verified=True
    ) is False
    assert not path.exists()
    assert record_skill(
        kind, key, "RAL 701605 / 9016", path=path,
        human_confirmed=True, readback_verified=True
    ) is True
    assert read_skill(kind, key, path=path) == "RAL 701605 / 9016"


def test_catalog_memory_separates_color_from_glazing(tmp_path):
    path = tmp_path / "skills.json"
    color_kind, color_key = skill_key(outside="Antracyt", inside="Biały")
    glass_kind, glass_key = skill_key(glazing_panes=2)
    assert record_skill(
        color_kind, color_key, "Antracyt / biały",
        human_confirmed=True, readback_verified=True, path=path
    )
    assert record_skill(
        glass_kind, glass_key, "2 szyby / 24mm",
        human_confirmed=True, readback_verified=True, path=path
    )
    assert read_skill(color_kind, color_key, path=path) == "Antracyt / biały"
    assert read_skill(glass_kind, glass_key, path=path) == "2 szyby / 24mm"


def test_reject_newlines_in_persisted_catalog_labels(tmp_path):
    import pytest
    kind, key = skill_key(glazing_panes=2)
    with pytest.raises(ValueError):
        record_skill(
            kind, key, "fake\ncommand",
            human_confirmed=True, readback_verified=True,
            path=tmp_path / "skills.json"
        )
