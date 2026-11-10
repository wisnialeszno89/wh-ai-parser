import pytest

from app.agent.offers.windowhub_double_sash_lab import simulate_double_sash
from app.simulator.window_simulator import WindowSimulator

REQUEST = {
    "width_mm": 1510, "height_mm": 1400, "mullion": "fixed", "split_from_left_mm": 755,
    "glazing_panes": 2, "left_opening": "DKL", "right_opening": "DKR",
}


@pytest.mark.parametrize(("left", "right", "expected", "invert"), [
    ("DKL", "DKR", {"left": "LEFT", "right": "RIGHT"}, "left"),
    ("DKR", "DKL", {"left": "RIGHT", "right": "LEFT"}, "right"),
])
def test_builds_frame_mullion_glass_and_per_sash_hardware(left, right, expected, invert):
    result = simulate_double_sash(REQUEST | {"left_opening": left, "right_opening": right})
    elements = {row["id"]: row for row in result["scene"]["elements"]}

    assert [row["stage"] for row in result["trace"]] == [
        "frame", "fixed_mullion", "sashes", "glazing", "hardware", f"inversion_{invert}",
    ]
    assert elements["mullion_1"]["offset_from_left_mm"] == 755
    for side, direction in expected.items():
        assert elements[f"glass_{side}"]["panes"] == 2
        assert elements[f"hardware_{side}"]["parent_id"] == f"sash_{side}"
        assert elements[f"sash_{side}"]["direction"] == direction
        assert elements[f"sash_{side}"]["inversion_checked"] is (side == invert)


def test_readback_rejects_an_inversion_that_did_not_take_effect(monkeypatch):
    original = WindowSimulator._apply_one

    def ignore_inversion(self, action):
        if action.action_type != "set_hardware_inversion":
            original(self, action)

    monkeypatch.setattr(WindowSimulator, "_apply_one", ignore_inversion)
    with pytest.raises(ValueError, match="skrzydła left"):
        simulate_double_sash(REQUEST)


def test_incomplete_double_sash_does_not_guess_a_split():
    with pytest.raises(ValueError, match="wymiar podziału"):
        simulate_double_sash(REQUEST | {"split_from_left_mm": None})
