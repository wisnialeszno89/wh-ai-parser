import pytest

from app.agent.offers.windowhub_hardware_direction import plan_hardware_inversion
from tools.test_single_sash_construction_lab import WindowSimulator, check_single_sash


def zirkon(opening):
    return {
        "position": "10.0", "construction": "F004 DK-Fenster",
        "opening": opening, "width_mm": 935, "height_mm": 1145,
    }


@pytest.mark.parametrize(("code", "direction"), [("DKL", "LEFT"), ("DKR", "RIGHT")])
@pytest.mark.parametrize("auto_direction", ["LEFT", "RIGHT"])
def test_zirkon_only_inverts_a_mismatch(code, direction, auto_direction):
    result = check_single_sash(zirkon(code), auto_direction=auto_direction)

    assert result["inversion_action"] == ("unchanged" if direction == auto_direction else "on")
    assert result["scene"]["opening"] == {"width": 935, "height": 1145}
    assert [element["kind"] for element in result["scene"]["elements"]] == ["FRAME", "SASH"]
    assert result["scene"]["elements"][1]["side"] == "center"
    assert result["scene"]["elements"][1]["direction"] == direction


def test_unapplied_inversion_fails_readback(monkeypatch):
    apply = WindowSimulator._apply_one

    def ignore_inversion(self, action):
        if action.action_type != "set_hardware_inversion":
            apply(self, action)

    monkeypatch.setattr(WindowSimulator, "_apply_one", ignore_inversion)
    with pytest.raises(ValueError, match="nie potwierdził wymaganego otwierania"):
        check_single_sash(zirkon("DKR"))


def test_unknown_automatic_direction_stops_for_review():
    with pytest.raises(ValueError, match="Brak jednoznacznego kierunku"):
        check_single_sash(zirkon("DKR"), auto_direction=None)


def test_inversion_plan_uses_observed_checkbox_state():
    assert plan_hardware_inversion("LEFT", "RIGHT", True) is False
    assert plan_hardware_inversion("LEFT", "LEFT", True) is None
    with pytest.raises(ValueError, match="stanu pola Inwersja"):
        plan_hardware_inversion("LEFT", "RIGHT", None)


def test_missing_direction_stops_without_guessing():
    with pytest.raises(ValueError, match="DKL albo DKR"):
        check_single_sash(zirkon("DK"))
