import pytest

from app.agent.offers.windowhub_single_sash_lab import simulate_single_tilt_turn
from tools.check_windowhub_components_lab import check_component_cases


def test_component_cases_read_back_both_packages_and_correct_inversion():
    cases = check_component_cases()
    assert len(cases) == 8
    assert {case["simulation"]["panes"] for case in cases} == {2, 3}
    inverted = 0
    for case in cases:
        result = case["simulation"]
        glass = next(item for item in result["scene"]["elements"] if item["kind"] == "GLASS")
        sash = next(item for item in result["scene"]["elements"] if item["kind"] == "SASH")
        assert glass["parent_id"] == sash["id"]
        assert glass["panes"] == case["request"]["glazing_panes"]
        assert sash["inversion_checked"] == (result["automatic_direction"] != result["direction"])
        inverted += sash["inversion_checked"]
    assert inverted == 4


def test_unknown_automatic_hardware_direction_requires_review():
    with pytest.raises(ValueError, match="kierunku okucia"):
        simulate_single_tilt_turn(
            {"width_mm": 1000, "height_mm": 1000, "opening": "DKR", "glazing_panes": 3},
            auto_direction=None,
        )
