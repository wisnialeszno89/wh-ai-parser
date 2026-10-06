from types import SimpleNamespace

from app.agent.learning.human_action_event import HumanActionEvent
from app.agent.learning.learning_session import LearningSession
from app.agent.learning.windowhub_learning_controller import (
    WindowHubLearningController,
)
from app.agent.learning.windowhub_mouse_observer import (
    GA_ROOT,
    GA_ROOTOWNER,
    WindowHubMouseObserver,
)
from app.agent.learning.workflow_memory_store import WorkflowMemoryStore
from app.agent.perception.interaction_capability import (
    InteractionCapability,
)
from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.screen_scene import ScreenScene


class FakeMouseObserver:
    def __init__(self):
        self.callback = None
        self.started = False
        self.stopped = False

    def start(self, callback):
        self.callback = callback
        self.started = True

    def stop(self):
        self.stopped = True


class FakeControlLoop:
    def __init__(self, scenes):
        self.scenes = list(scenes)
        self.calls = 0

    def observe_scene(self):
        self.calls += 1
        return self.scenes[min(self.calls - 1, len(self.scenes) - 1)]


class FakeFocusHandler:
    def __init__(self, success=True):
        self.success = success
        self.called = False

    def execute(self, preparation):
        self.called = True
        return SimpleNamespace(
            success=self.success,
            reason="ok" if self.success else "failed",
        )


def _scene(label="Zapisz"):
    observation = SimpleNamespace(
        state=SimpleNamespace(
            active_application="WindowHub",
            active_window_title="Okna - OFR/1",
        )
    )
    button = ScreenElement(
        kind="button",
        label=label,
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


def test_windowhub_mouse_observer_converts_and_scopes_click():
    observer = FakeMouseObserver()
    wrapped = WindowHubMouseObserver(
        mouse_observer=observer,
    )

    captured = []
    wrapped.start(captured.append)

    assert observer.started

    original = wrapped._windowhub_local_position
    wrapped._windowhub_local_position = (
        lambda x, y: (x - 1000, y - 100)
    )

    observer.callback(
        HumanActionEvent(
            action_type="click",
            x=1100,
            y=200,
        )
    )

    assert len(captured) == 1
    assert captured[0].x == 100
    assert captured[0].y == 100
    assert captured[0].metadata["scope"] == "WindowHub"

    wrapped._windowhub_local_position = original
    wrapped.stop()

    assert observer.stopped


def test_windowhub_mouse_observer_ignores_click_outside_windowhub():
    observer = FakeMouseObserver()
    wrapped = WindowHubMouseObserver(
        mouse_observer=observer,
    )

    captured = []
    wrapped.start(captured.append)
    wrapped._windowhub_local_position = lambda x, y: None

    observer.callback(
        HumanActionEvent(
            action_type="click",
            x=10,
            y=10,
        )
    )

    assert captured == []


def test_windowhub_mouse_observer_accepts_windowhub_owned_dialog():
    class FakeUser32:
        def GetAncestor(self, hwnd, flags):
            if flags == GA_ROOT:
                return 9000
            if flags == GA_ROOTOWNER:
                return 7146954
            raise AssertionError(flags)

    assert WindowHubMouseObserver._topmost_belongs_to_windowhub(
        topmost=9001,
        windowhub_hwnd=7146954,
        user32=FakeUser32(),
    )


def test_windowhub_mouse_observer_rejects_unrelated_dialog():
    class FakeUser32:
        def GetAncestor(self, hwnd, flags):
            if flags == GA_ROOT:
                return 9000
            if flags == GA_ROOTOWNER:
                return 8000
            raise AssertionError(flags)

    assert not WindowHubMouseObserver._topmost_belongs_to_windowhub(
        topmost=9001,
        windowhub_hwnd=7146954,
        user32=FakeUser32(),
    )


def test_windowhub_learning_controller_starts_from_real_semantic_scene(monkeypatch):
    mouse = FakeMouseObserver()
    focus = FakeFocusHandler()
    scenes = [_scene(), _scene("Zapisane")]
    loop = FakeControlLoop(scenes)

    monkeypatch.setattr(
        WindowHubMouseObserver,
        "_windowhub_local_position",
        staticmethod(lambda x, y: (x, y)),
    )

    controller = WindowHubLearningController(
        learning_session=LearningSession(),
        observer=WindowHubMouseObserver(mouse_observer=mouse),
        workflow_memory_store=WorkflowMemoryStore(),
        control_loop=loop,
        focus_handler=focus,
    )

    controller.start(
        workflow_id="wh-wf",
        name="Zapisz ofertę",
        trigger="zapisz ofertę",
    )

    assert focus.called
    assert mouse.started
    assert loop.calls >= 2 or loop.calls == 1

    # Simulate the scoped observer producing a local WindowHub click.
    mouse.callback(
        HumanActionEvent(
            action_type="click",
            x=120,
            y=120,
        )
    )

    # Avoid relying on another scene provider call in this unit test.
    workflow = controller.finish()

    assert workflow.application == "WindowHub"
    assert len(workflow.steps) == 1
    assert workflow.steps[0].action.target == "Zapisz"
    assert workflow.steps[0].before.elements[0]["label"] == "Zapisz"
    assert workflow.steps[0].after.elements[0]["label"] == "Zapisane"
