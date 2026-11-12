import pytest

from app.agent.offers.windowhub_door_lab import simulate_entrance_door
from app.simulator.window_simulator import WindowSimulator


REQUEST = {"width_mm": 1000, "height_mm": 2000, "opening": "DL", "swing": "inward", "infill": "solid_panel"}


@pytest.mark.parametrize(("code", "swing", "direction"), [("DL", "inward", "LEFT"), ("DR", "outward", "RIGHT")])
def test_door_scene_preserves_swing_and_uses_solid_panel_and_door_hinges(code, swing, direction):
    result = simulate_entrance_door(REQUEST | {"opening": code, "swing": swing})

    assert [row["stage"] for row in result["trace"]] == ["frame", "door_leaf", "solid_panel", "door_hinges"]
    frame, leaf, panel, hinges = result["scene"]["elements"]
    assert [element["kind"] for element in (frame, leaf, panel, hinges)] == [
        "FRAME", "DOOR_LEAF", "SOLID_PANEL", "DOOR_HINGES",
    ]
    assert leaf["opening"] == "TURN"
    assert (leaf["direction"], leaf["swing"]) == (direction, swing)
    assert panel["parent_id"] == hinges["parent_id"] == leaf["id"]


@pytest.mark.parametrize(("change", "message"), [
    ({"swing": None}, "do wewnątrz czy na zewnątrz"),
    ({"infill": None}, "pełny panel"),
    ({"opening": "DKL"}, "DL albo DR"),
    ({"glazing_panes": 2}, "pakietu szybowego"),
])
def test_door_requires_explicit_consistent_inputs(change, message):
    with pytest.raises(ValueError, match=message):
        simulate_entrance_door(REQUEST | change)


def test_door_readback_detects_missing_hinges(monkeypatch):
    original = WindowSimulator._apply_one

    def skip_hinges(self, action):
        if action.action_type != "add_door_hinges":
            original(self, action)

    monkeypatch.setattr(WindowSimulator, "_apply_one", skip_hinges)
    with pytest.raises(ValueError, match="nie potwierdził kompletnej konstrukcji"):
        simulate_entrance_door(REQUEST)
