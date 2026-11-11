import pytest

from app.agent.offers.windowhub_glass_selection import select_glass_package

PACKAGE = {"id": "test-48", "panes": 3, "thickness_mm": 48, "ug": 0.5,
           "warm_edge": True, "spacer": "Swisspacer Ultimate"}


def test_exact_numeric_and_text_requirements_select_one_record():
    result = select_glass_package(
        {"panes": 3, "ug": "0,50", "warm_edge": True, "spacer": "  SWISSPACER   Ultimate "}, [PACKAGE],
    )
    assert result["selected"]["id"] == PACKAGE["id"]


@pytest.mark.parametrize(("field", "value"), [
    ("panes", 2), ("thickness_mm", 44), ("ug", 0.6),
    ("warm_edge", False), ("spacer", "aluminium"),
])
def test_similar_record_is_rejected_when_a_requested_property_differs(field, value):
    result = select_glass_package({field: value}, [PACKAGE])
    assert result["status"] == "review"
    assert result["requirements"] == {field: value}
    assert result["rejected"] == [{"id": "test-48", "different_fields": [field]}]
    assert "selected" not in result


def test_duplicate_matches_or_unknown_candidate_prevent_arbitrary_selection():
    for other in (dict(PACKAGE, id="another"), {"id": "unknown"}):
        result = select_glass_package({"panes": 3}, [PACKAGE, other])
        assert result["status"] == "review"
        assert "selected" not in result


@pytest.mark.parametrize("requirements", [{"panes": True}, {"ug": "NaN"}, {"ug": -1}, {"warm_edge": "yes"}, {"unknown": 3}])
def test_invalid_requirements_are_not_silently_ignored(requirements):
    with pytest.raises(ValueError):
        select_glass_package(requirements, [PACKAGE])
