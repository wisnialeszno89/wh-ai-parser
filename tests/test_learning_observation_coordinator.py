from types import SimpleNamespace

import pytest

from app.agent.learning.human_action_event import HumanActionEvent
from app.agent.learning.human_action_observer import (
    HumanActionObserver,
)
from app.agent.learning.learning_observation_coordinator import (
    LearningObservationCoordinator,
)
from app.agent.learning.learning_session import LearningSession
from app.agent.perception.interaction_capability import (
    InteractionCapability,
)
from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.screen_scene import ScreenScene


class FakeObserver(HumanActionObserver):
    def __init__(self):
        self.callback = None
        self.started = False
        self.stopped = False

    def start(self, callback):
        self.callback = callback
        self.started = True

    def stop(self):
        self.stopped = True

    def emit(self, event):
        assert self.callback is not None
        self.callback(event)


def _scene():
    observation = SimpleNamespace(
        state=SimpleNamespace(
            active_application="TestApp",
            active_window_title="Test Window",
        )
    )
    button = ScreenElement(
        kind="button",
        label="Zapisz",
        x=100,
        y=100,
        width=100,
        height=40,
        confidence=0.95,
        interaction_capability=InteractionCapability.CLICKABLE,
    )
    return ScreenScene(
        observation=observation,
        elements=(button,),
    )


def test_coordinator_requires_initial_semantic_scene():
    session = LearningSession()
    session.start(
        workflow_id="wf",
        name="Test",
        trigger="test",
        application="TestApp",
    )

    observer = FakeObserver()
    coordinator = LearningObservationCoordinator(
        session=session,
        observer=observer,
        scene_provider=lambda: None,
    )

    with pytest.raises(RuntimeError, match="semantic scene"):
        coordinator.start()

    assert not observer.started


def test_coordinator_translates_human_click_to_learned_step():
    scenes = [_scene(), _scene()]
    observer = FakeObserver()
    session = LearningSession()

    session.start(
        workflow_id="wf-coordinator",
        name="Zapisz",
        trigger="zapisz",
        application="TestApp",
    )

    coordinator = LearningObservationCoordinator(
        session=session,
        observer=observer,
        scene_provider=lambda: scenes.pop(0),
    )
    coordinator.start()

    observer.emit(
        HumanActionEvent(
            action_type="click",
            x=120,
            y=120,
        )
    )

    workflow = session.finish()

    assert observer.started
    assert len(workflow.steps) == 1
    assert workflow.steps[0].action.name == "click_screen_element"
    assert workflow.steps[0].action.target == "Zapisz"


def test_coordinator_stop_stops_platform_observer():
    observer = FakeObserver()
    session = LearningSession()
    session.start(
        workflow_id="wf-stop",
        name="Test",
        trigger="test",
        application="TestApp",
        scene=_scene(),
    )

    coordinator = LearningObservationCoordinator(
        session=session,
        observer=observer,
        scene_provider=lambda: _scene(),
    )
    coordinator.start()
    coordinator.stop()

    assert observer.started
    assert observer.stopped
