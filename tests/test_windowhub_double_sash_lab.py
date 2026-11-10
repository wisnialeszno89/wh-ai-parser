import pytest

from app.agent.offers.windowhub_double_sash_lab import simulate_double_sash, simulate_stulp
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


@pytest.mark.parametrize(("active", "passive", "direction"), [
    ("left", "right", "LEFT"),
    ("right", "left", "RIGHT"),
])
def test_stulp_build_attaches_mullion_and_latch_only_to_passive_sash(active, passive, direction):
    result = simulate_stulp(REQUEST | {
        "width_mm": 1200, "height_mm": 1000, "split_from_left_mm": 600,
        "mullion": "movable", "active_side": active,
    })
    elements = {row["id"]: row for row in result["scene"]["elements"]}

    assert "mullion_1" not in elements
    assert elements["stulp_1"]["parent_id"] == f"sash_{passive}"
    assert elements["stulp_1"]["offset_from_left_mm"] == 600
    assert elements[f"latch_{passive}"]["parent_id"] == f"sash_{passive}"
    assert elements[f"hardware_{active}"]["parent_id"] == f"sash_{active}"
    assert f"hardware_{passive}" not in elements
    assert result["final_directions"] == {active: direction}


def test_wrong_stulp_mount_is_rejected_before_installing_hardware(monkeypatch):
    original = WindowSimulator._apply_one

    def put_mullion_on_active_sash(self, action):
        if action.action_type == "attach_movable_mullion":
            action.target_id = "left"
        original(self, action)

    monkeypatch.setattr(WindowSimulator, "_apply_one", put_mullion_on_active_sash)
    with pytest.raises(ValueError, match="must belong to the passive sash"):
        simulate_stulp(REQUEST | {"mullion": "movable", "active_side": "left"})
