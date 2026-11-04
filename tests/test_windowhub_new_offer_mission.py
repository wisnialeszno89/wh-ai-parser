from types import SimpleNamespace
import pytest

from app.agent.offers.windowhub_new_offer_mission import (
    NewWindowOfferGoal, NewWindowOfferMissionPlanner, OfferDecision,
)
from app.agent.offers.windowhub_offer_form_map import WindowHubFormStep
from app.agent.offers.windowhub_position_mission import WindowPositionRequest


def _scene(*, application="Okna.exe", title="", elements=()):
    return SimpleNamespace(
        observation=SimpleNamespace(
            state=SimpleNamespace(active_application=application, active_window_title=title)
        ),
        elements=elements,
    )


class StubMap:
    def __init__(self, step=None, width="1000", height="1000"):
        self.step = step
        self.width = width
        self.height = height

    def inspect(self, scene):
        if self.step is None:
            return None

        def field(name):
            value = {"width_1": self.width, "height_1": self.height}.get(name)
            if value is None:
                return None
            return SimpleNamespace(
                is_unique=True, enabled=True,
                element=SimpleNamespace(metadata={"current_value": value}),
            )
        return SimpleNamespace(step=self.step, field=field)


GOAL = NewWindowOfferGoal(
    WindowPositionRequest(quantity=1, width_mm=1230, height_mm=1478)
)


def test_goal_rejects_unapproved_customer_policy():
    with pytest.raises(ValueError):
        NewWindowOfferGoal(GOAL.position, customer_policy="random_real_customer")


def test_rejects_other_application():
    decision = NewWindowOfferMissionPlanner(StubMap()).decide(
        GOAL, _scene(application="Code.exe")
    )
    assert decision.decision is OfferDecision.STOP_WRONG_ENVIRONMENT


def test_identifies_document_properties():
    decision = NewWindowOfferMissionPlanner(StubMap()).decide(
        GOAL, _scene(title="Właściwości dokumentu")
    )
    assert decision.decision is OfferDecision.SELECT_TEST_CUSTOMER
    assert decision.executable is False


def test_recognizes_position_wizard():
    decision = NewWindowOfferMissionPlanner(StubMap(WindowHubFormStep.POSITION)).decide(
        GOAL, _scene(title="Dodawanie nowej pozycji")
    )
    assert decision.decision is OfferDecision.DELEGATE_POSITION


def test_dimensions_width_then_height_then_next():
    scene = _scene(title="Wielkość okna")
    first = NewWindowOfferMissionPlanner(
        StubMap(WindowHubFormStep.DIMENSIONS)
    ).decide(GOAL, scene)
    assert first.decision is OfferDecision.SET_WIDTH
    assert first.field_name == "width_1"
    assert first.desired_value == 1230
    assert first.executable is False

    second = NewWindowOfferMissionPlanner(
        StubMap(WindowHubFormStep.DIMENSIONS, width="1230")
    ).decide(GOAL, scene)
    assert second.decision is OfferDecision.SET_HEIGHT
    assert second.field_name == "height_1"
    assert second.desired_value == 1478

    third = NewWindowOfferMissionPlanner(
        StubMap(WindowHubFormStep.DIMENSIONS, width="1230", height="1478")
    ).decide(GOAL, scene)
    assert third.decision is OfferDecision.ADVANCE_TO_PARAMETERS


def test_color_requires_verified_catalog_action():
    decision = NewWindowOfferMissionPlanner(
        StubMap(WindowHubFormStep.BASIC_PARAMETERS)
    ).decide(GOAL, _scene(title="Podstawowe parametry okna"))
    assert decision.decision is OfferDecision.SELECT_PROFILE_COLOR
    assert decision.executable is False
    assert decision.desired_value == ("biały", "antracyt")
