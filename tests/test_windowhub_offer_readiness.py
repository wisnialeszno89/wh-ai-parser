from types import SimpleNamespace

import pytest

from app.agent.offers.windowhub_new_offer_mission import (
    NewWindowOfferGoal, NewWindowOfferMissionPlanner, OfferDecision,
)
from app.agent.offers.windowhub_position_mission import WindowPositionRequest
from tools.check_windowhub_offer_readiness import run_access_cases, scene


@pytest.mark.parametrize("title", ["Logowanie", "Anmeldung", "Login", "WindowHub - logowanie"])
def test_login_precedes_form_resolution(title):
    class NoFormInspection:
        def inspect(self, observation):
            raise AssertionError("Login must pause before looking for offer actions")
    decision = NewWindowOfferMissionPlanner(NoFormInspection()).decide(
        NewWindowOfferGoal(WindowPositionRequest(1, 1100, 1000)), scene(title=title))
    assert decision.decision is OfferDecision.WAIT_USER_LOGIN
    assert decision.executable is False and decision.desired_value is None


def test_resume_uses_current_dimensions_instead_of_restarting_offer():
    from tests.test_windowhub_new_offer_mission import StubMap
    from app.agent.offers.windowhub_offer_form_map import WindowHubFormStep
    goal = NewWindowOfferGoal(WindowPositionRequest(1, 1100, 1000))
    planner = NewWindowOfferMissionPlanner(StubMap(WindowHubFormStep.DIMENSIONS, width="1100", height="900"))
    assert planner.decide(goal, scene(title="Logowanie")).decision is OfferDecision.WAIT_USER_LOGIN
    result = planner.decide(goal, scene(title="Wielkość okna"))
    assert result.decision is OfferDecision.SET_HEIGHT and result.desired_value == 1000


@pytest.mark.parametrize("visible,source,expected", [
    (True, "windowhub_ui_automation", OfferDecision.WAIT_USER_LOGIN),
    (False, "windowhub_ui_automation", OfferDecision.SELECT_TEST_CUSTOMER),
    (True, "untrusted_text", OfferDecision.SELECT_TEST_CUSTOMER),
])
def test_password_detection_requires_visible_native_evidence(visible, source, expected):
    item = SimpleNamespace(kind="edit", label="Passwort:", metadata={"source":source, "uia_visible":visible})
    result = NewWindowOfferMissionPlanner().decide(
        NewWindowOfferGoal(WindowPositionRequest(1, 1100, 1000)),
        scene(title="Właściwości dokumentu", elements=(item,)))
    assert result.decision is expected


def test_readiness_scenarios():
    assert len(run_access_cases()) == 5
