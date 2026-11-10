import pytest

from tools.test_single_sash_construction_lab import SemanticWindowSimulator, check_single_sash


def zirkon(opening):
    return {
        "position": "10.0", "construction": "F004 DK-Fenster",
        "opening": opening, "width_mm": 935, "height_mm": 1145,
    }


@pytest.mark.parametrize(("code", "direction"), [("DKL", "LEFT"), ("DKR", "RIGHT")])
def test_zirkon_direction_selects_different_tool_but_keeps_one_central_sash(code, direction):
    result = check_single_sash(zirkon(code))

    assert result["tool"] == f"tilt_turn_{direction.lower()}_tool"
    assert result["scene"]["opening"] == {"width": 935, "height": 1145}
    assert [element["kind"] for element in result["scene"]["elements"]] == ["FRAME", "SASH"]
    assert result["scene"]["elements"][1]["side"] == "center"
    assert result["scene"]["elements"][1]["direction"] == direction


def test_wrong_tool_fails_readback(monkeypatch):
    build = SemanticWindowSimulator.build_actions

    def select_wrong_tool(self, desired, topology):
        actions = build(self, desired, topology)
        actions[-2].tool_name = "tilt_turn_right_tool"
        return actions

    monkeypatch.setattr(SemanticWindowSimulator, "build_actions", select_wrong_tool)
    with pytest.raises(ValueError, match="nie potwierdził wymaganego otwierania"):
        check_single_sash(zirkon("DKL"))


def test_missing_direction_stops_without_guessing():
    with pytest.raises(ValueError, match="DKL albo DKR"):
        check_single_sash(zirkon("DK"))
