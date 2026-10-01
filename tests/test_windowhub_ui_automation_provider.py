from types import SimpleNamespace

from app.agent.environment.environment_observation import (
    EnvironmentObservation,
)
from app.agent.environment.environment_state import (
    EnvironmentState,
)
from app.agent.perception.interaction_capability import (
    InteractionCapability,
)
from app.agent.perception.perception_engine import (
    PerceptionEngine,
)
from app.agent.perception.screen_element import (
    ScreenElement,
)
from app.agent.perception.target_resolver import (
    TargetResolver,
)
from app.agent.perception.windowhub_ui_automation_provider import (
    WindowHubUIAutomationProvider,
)
from app.agent.perception.windowhub_vision_provider import (
    WindowHubVisionProvider,
)
from app.runtime.execution.vision.models.logical_object import (
    LogicalObject,
)
from app.runtime.execution.vision.models.rect import (
    Rect,
)
from app.runtime.execution.vision.models.tracked_object import (
    TrackedObject,
    TrackedObjectStatus,
)


class FakeUIAItem:
    def __init__(
        self,
        *,
        name,
        control_type="Button",
        automation_id="",
        enabled=True,
        visible=True,
        left=120,
        top=220,
        width=100,
        height=80,
        runtime_id=(1, 2, 3),
    ):
        self.element_info = SimpleNamespace(
            name=name,
            control_type=control_type,
            automation_id=automation_id,
            enabled=enabled,
            visible=visible,
            runtime_id=runtime_id,
        )
        self._rectangle = SimpleNamespace(
            left=left,
            top=top,
            width=lambda: width,
            height=lambda: height,
        )

    def rectangle(self):
        return self._rectangle


class FakeUIAWindow:
    def __init__(self, items, title="Okna - WindowHub"):
        self._items = tuple(items)
        self._title = title

    def window_text(self):
        return self._title

    def descendants(self):
        return self._items


class FakeDesktop:
    def __init__(self, window):
        self._window = window

    def get_active(self):
        return self._window


def make_observation(tracked_objects=()):
    return EnvironmentObservation(
        state=EnvironmentState(
            active_window_title="Okna - WindowHub",
        ),
        metadata={
            "window_rect": SimpleNamespace(
                left=100,
                top=200,
                width=1000,
                height=800,
            ),
            "execution_runtime": {
                "robot_tracked_objects": tuple(tracked_objects),
            },
        },
    )


def make_tracked(
    tracked_id="TO-0001",
    *,
    x=30,
    y=40,
    width=20,
    height=20,
):
    return TrackedObject(
        id=tracked_id,
        object=LogicalObject(
            bounds=Rect(
                x=x,
                y=y,
                width=width,
                height=height,
            ),
            root_contour_index=1,
            member_contour_indices=(1,),
        ),
        control_type="icon",
        confidence=0.95,
        consecutive_observations=3,
        status=TrackedObjectStatus.STABLE,
        stability=1.0,
    )


def test_ui_automation_provider_exposes_semantic_name_and_capability():
    item = FakeUIAItem(
        name="NOWA OFERTA",
        automation_id="Nowa_oferta",
        left=120,
        top=220,
        width=110,
        height=110,
    )
    desktop = FakeDesktop(
        FakeUIAWindow((item,))
    )
    tracked = make_tracked(
        x=30,
        y=40,
        width=20,
        height=20,
    )

    elements = WindowHubUIAutomationProvider(
        desktop_factory=lambda: desktop,
    ).perceive(
        make_observation((tracked,))
    )

    assert len(elements) == 1
    element = elements[0]

    assert element.label == "NOWA OFERTA"
    assert element.interaction_capability is InteractionCapability.CLICKABLE
    assert element.metadata["automation_id"] == "Nowa_oferta"
    assert element.metadata["tracked_object_id"] == "TO-0001"
    assert element.x == 20
    assert element.y == 20
    assert element.width == 110
    assert element.height == 110


def test_ui_automation_provider_rejects_ambiguous_visual_correlation():
    item = FakeUIAItem(
        name="NOWA OFERTA",
        left=100,
        top=200,
        width=200,
        height=200,
    )
    desktop = FakeDesktop(FakeUIAWindow((item,)))

    tracked_a = make_tracked("TO-0001", x=20, y=20)
    tracked_b = make_tracked("TO-0002", x=120, y=120)

    elements = WindowHubUIAutomationProvider(
        desktop_factory=lambda: desktop,
    ).perceive(
        make_observation((tracked_a, tracked_b))
    )

    assert len(elements) == 1
    assert "tracked_object_id" not in elements[0].metadata
    assert elements[0].metadata["correlation"] == "unresolved"


def test_ui_automation_provider_disabled_control_is_not_interactive():
    item = FakeUIAItem(
        name="Zamień miejscami",
        automation_id="swap",
        enabled=False,
    )
    desktop = FakeDesktop(FakeUIAWindow((item,)))

    elements = WindowHubUIAutomationProvider(
        desktop_factory=lambda: desktop,
    ).perceive(
        make_observation()
    )

    assert len(elements) == 1
    assert (
        elements[0].interaction_capability
        is InteractionCapability.NOT_INTERACTIVE
    )


def test_ui_automation_provider_semantic_target_can_fuse_with_visual_identity():
    visual = ScreenElement(
        kind="icon",
        confidence=0.80,
        x=30,
        y=40,
        width=20,
        height=20,
        metadata={
            "source": "windowhub_vision_pipeline",
            "tracked_object_id": "TO-0001",
        },
    )

    item = FakeUIAItem(
        name="NOWA OFERTA",
        automation_id="Nowa_oferta",
        left=120,
        top=220,
        width=110,
        height=110,
    )

    desktop = FakeDesktop(FakeUIAWindow((item,)))
    provider = WindowHubUIAutomationProvider(
        desktop_factory=lambda: desktop,
    )

    class StaticVisionProvider:
        def perceive(self, observation):
            return (visual,)

    scene = PerceptionEngine(
        providers=(
            StaticVisionProvider(),
            provider,
        ),
    ).perceive(
        make_observation((make_tracked(),))
    )

    assert len(scene.elements) == 1

    fused = scene.elements[0]
    assert fused.label == "NOWA OFERTA"
    assert (
        fused.interaction_capability
        is InteractionCapability.CLICKABLE
    )
    assert (
        (fused.metadata or {}).get("tracked_object_id")
        == "TO-0001"
    )

    resolution = TargetResolver().resolve(
        scene,
        "NOWA OFERTA",
    )

    assert resolution.resolved is True
    assert resolution.element is fused
    assert resolution.score == 1.0


def test_ui_automation_provider_does_not_expose_automation_id_as_label():
    item = FakeUIAItem(
        name="",
        automation_id="IDC_NEW",
    )
    desktop = FakeDesktop(
        FakeUIAWindow(
            (item,),
            title="Okna - WindowHub",
        )
    )

    elements = WindowHubUIAutomationProvider(
        desktop_factory=lambda: desktop,
    ).perceive(
        make_observation()
    )

    assert elements == ()
