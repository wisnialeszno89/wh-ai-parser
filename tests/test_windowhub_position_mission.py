from types import SimpleNamespace

import pytest

from app.agent.offers.windowhub_offer_form_map import WindowHubFormStep
from app.agent.offers.windowhub_position_mission import (
    MissionDecision,
    WindowPositionMissionPlanner,
    WindowPositionRequest,
)


class StubMap:
    def __init__(self, step, quantity="2", selected=True):
        self.step = step
        self.quantity = quantity
        self.selected = selected

    def inspect(self, scene):
        if self.step is None:
            return None

        def field(name):
            if name == "quantity_input":
                return SimpleNamespace(
                    is_unique=True,
                    enabled=True,
                    element=SimpleNamespace(metadata={"current_value": self.quantity}),
                )
            if name == "item_type_window":
                return SimpleNamespace(
                    is_unique=True,
                    enabled=True,
                    element=SimpleNamespace(metadata={"uia_selected": self.selected}),
                )
            return None

        return SimpleNamespace(step=self.step, field=field)


REQUEST = WindowPositionRequest(quantity=2, width_mm=1200, height_mm=1400)


@pytest.mark.parametrize("field", ["quantity", "width_mm", "height_mm"])
@pytest.mark.parametrize("invalid", [0, -1, True, "2", None])
def test_invalid_business_request_rejected(field, invalid):
    kwargs = {"quantity": 2, "width_mm": 1200, "height_mm": 1400}
    kwargs[field] = invalid
    with pytest.raises(ValueError):
        WindowPositionRequest(**kwargs)


def test_mission_writes_quantity_before_navigating():
    planner = WindowPositionMissionPlanner(StubMap(WindowHubFormStep.POSITION, quantity="1"))
    instruction = planner.decide(REQUEST, object())
    assert instruction.decision is MissionDecision.WRITE_QUANTITY
    assert instruction.executable is True


def test_mission_navigates_only_when_quantity_matches():
    planner = WindowPositionMissionPlanner(StubMap(WindowHubFormStep.POSITION, quantity="2"))
    instruction = planner.decide(REQUEST, object())
    assert instruction.decision is MissionDecision.NAVIGATE_TO_DIMENSIONS
    assert instruction.executable is True


def test_mission_rejects_unselected_window():
    planner = WindowPositionMissionPlanner(StubMap(WindowHubFormStep.POSITION, selected=False))
    instruction = planner.decide(REQUEST, object())
    assert instruction.decision is MissionDecision.STOP_UNSUPPORTED
    assert instruction.executable is False


@pytest.mark.parametrize(
    ("step", "decision"),
    [
        (WindowHubFormStep.DIMENSIONS, MissionDecision.COLLECT_DIMENSIONS_CAPABILITY),
        (WindowHubFormStep.BASIC_PARAMETERS, MissionDecision.COLLECT_BASIC_PARAMETERS_CAPABILITY),
        (WindowHubFormStep.GLAZING, MissionDecision.COLLECT_GLAZING_CAPABILITY),
        (WindowHubFormStep.HARDWARE, MissionDecision.COLLECT_HARDWARE_CAPABILITY),
        (WindowHubFormStep.SILL, MissionDecision.STOP_UNSUPPORTED),
        (None, MissionDecision.STOP_WRONG_ENVIRONMENT),
    ],
)
def test_mission_reports_unproven_capabilities_without_acting(step, decision):
    instruction = WindowPositionMissionPlanner(StubMap(step)).decide(REQUEST, object())
    assert instruction.decision is decision
    assert instruction.executable is False
