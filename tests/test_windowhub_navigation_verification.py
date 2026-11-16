"""Safety tests for independent, fresh WindowHub navigation readback."""
from types import SimpleNamespace as N

from app.agent.environment.environment_observation import EnvironmentObservation
from app.agent.environment.environment_state import EnvironmentState
from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.screen_scene import ScreenScene
from app.agent.runtime.windowhub_navigation_verification import verified_navigation_transition


def scene(title, *, selected=None):
    tabs = ()
    if selected is not None:
        tabs = (ScreenElement(
            kind="tabitem", label="Start1", x=50, y=137, width=81, height=21,
            metadata={"source": "windows_ui_automation", "uia_visible": True, "uia_selected": selected},
        ),)
    return ScreenScene(
        observation=EnvironmentObservation(state=EnvironmentState(
            active_application="Okna.exe", active_window_title=title
        )),
        elements=tabs,
    )


def result(executed):
    return N(last_execution_result=N(last_attempt=N(
        execution_result=N(metadata={"executed": executed})
    )))


def test_tab_transition_requires_executed_and_selected_fresh_readback():
    assert verified_navigation_transition(result(True), scene("Okna - Start1", selected=True), expected_stage="start")
    assert not verified_navigation_transition(result(False), scene("Okna - Start1", selected=True), expected_stage="start")
    assert not verified_navigation_transition(result(True), scene("Okna - Start1", selected=False), expected_stage="start")
    assert not verified_navigation_transition(result(True), scene("Okna - OFR/4670-", selected=True), expected_stage="start")


def test_new_document_transition_requires_execution_and_fresh_stage():
    assert verified_navigation_transition(result(True), scene("Właściwości dokumentu"), expected_stage="document_properties")
    assert not verified_navigation_transition(result(False), scene("Właściwości dokumentu"), expected_stage="document_properties")
    assert not verified_navigation_transition(result(True), scene("Okna - Start1"), expected_stage="document_properties")


def test_unsupported_stage_rejected():
    import pytest
    with pytest.raises(ValueError):
        verified_navigation_transition(result(True), scene("Okna - Start1", selected=True), expected_stage="modifier")
