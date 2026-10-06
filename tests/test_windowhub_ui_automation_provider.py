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
        value=None,
        parent=None,
        class_name="",
    ):
        self.element_info = SimpleNamespace(
            name=name,
            control_type=control_type,
            automation_id=automation_id,
            enabled=enabled,
            visible=visible,
            runtime_id=runtime_id,
            rich_text=value,
            class_name=class_name,
        )
        self._parent = parent
        self._rectangle = SimpleNamespace(
            left=left,
            top=top,
            width=lambda: width,
            height=lambda: height,
        )

    def rectangle(self):
        return self._rectangle

    def parent(self):
        return self._parent


class FakeUIAWindow:
    def __init__(self, items, title="Okna - WindowHub"):
        self._items = tuple(items)
        self._title = title

    def window_text(self):
        return self._title

    def descendants(self):
        return self._items


class FakeDesktop:
    def __init__(self, window, windows_by_handle=None):
        self._window = window
        self._windows_by_handle = dict(windows_by_handle or {})

    def get_active(self):
        return self._window

    def window(self, *, handle):
        return self._windows_by_handle[handle]


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


def test_ui_automation_provider_accepts_window_title_with_trailing_whitespace():
    item = FakeUIAItem(
        name="Dodaj",
        automation_id="Dodaj",
    )
    desktop = FakeDesktop(
        FakeUIAWindow(
            (item,),
            title="Okna - WindowHub ",
        )
    )

    elements = WindowHubUIAutomationProvider(
        desktop_factory=lambda: desktop,
    ).perceive(
        make_observation()
    )

    assert len(elements) == 1
    assert elements[0].label == "Dodaj"


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



def test_ui_automation_provider_resolves_generic_layout_item_from_neighbor_text():
    label = FakeUIAItem(
        name="Szerokość",
        control_type="Text",
        left=110,
        top=220,
        width=90,
        height=24,
    )
    editor = FakeUIAItem(
        name="LayoutItem",
        control_type="Edit",
        left=210,
        top=220,
        width=120,
        height=30,
    )

    desktop = FakeDesktop(
        FakeUIAWindow(
            (label, editor),
            title="Okna - WindowHub",
        )
    )

    elements = WindowHubUIAutomationProvider(
        desktop_factory=lambda: desktop,
    ).perceive(
        make_observation()
    )

    assert len(elements) == 1
    assert elements[0].kind == "edit"
    assert elements[0].label == "Szerokość"
    assert (
        elements[0].metadata["semantic_label_source"]
        == "uia_text_neighbor"
    )


def test_ui_automation_provider_rejects_ambiguous_neighbor_labels():
    label_a = FakeUIAItem(
        name="Szerokość",
        control_type="Text",
        left=110,
        top=220,
        width=90,
        height=24,
    )
    label_b = FakeUIAItem(
        name="Wysokość",
        control_type="Text",
        left=110,
        top=250,
        width=90,
        height=24,
    )
    editor = FakeUIAItem(
        name="LayoutItem",
        control_type="Edit",
        left=210,
        top=235,
        width=120,
        height=30,
    )

    desktop = FakeDesktop(
        FakeUIAWindow(
            (label_a, label_b, editor),
            title="Okna - WindowHub",
        )
    )

    elements = WindowHubUIAutomationProvider(
        desktop_factory=lambda: desktop,
    ).perceive(
        make_observation()
    )

    assert elements == ()


def test_ui_automation_provider_exposes_current_editor_value():
    item = FakeUIAItem(
        name="Szerokość",
        control_type="Edit",
        value="1230",
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

    assert len(elements) == 1
    assert elements[0].metadata["current_value"] == "1230"


def test_ui_automation_provider_exposes_explicit_document_scope():
    tab_host = FakeUIAItem(
        name="",
        control_type="Tab",
        class_name="Afx:TabWnd",
    )
    document_tab = FakeUIAItem(
        name="OFR/4024",
        control_type="TabItem",
        parent=tab_host,
    )
    item = FakeUIAItem(
        name="Szerokość",
        control_type="Edit",
        parent=document_tab,
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

    assert len(elements) == 1
    assert elements[0].metadata["document_scope"] == "OFR/4024"


def test_ui_automation_provider_leaves_document_scope_unknown_without_tab_ancestry():
    container = FakeUIAItem(
        name="Konstrukcja",
        control_type="Pane",
        class_name="Afx:Pane",
    )
    item = FakeUIAItem(
        name="Szerokość",
        control_type="Edit",
        parent=container,
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

    assert len(elements) == 1
    assert elements[0].metadata["document_scope"] is None


def test_ui_automation_provider_exposes_bounded_ancestor_context():
    container = FakeUIAItem(
        name="Konstrukcja",
        control_type="Pane",
        class_name="Afx:Pane",
    )
    item = FakeUIAItem(
        name="Szerokość",
        control_type="Edit",
        parent=container,
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

    assert len(elements) == 1
    assert elements[0].metadata["uia_ancestor_context"] == (
        ("Pane", "Afx:Pane", "Konstrukcja"),
    )


def test_ui_automation_provider_includes_windowhub_owned_foreground_dialog():
    root_item = FakeUIAItem(
        name="Dodaj",
        left=110,
        top=210,
        width=70,
        height=40,
    )
    dialog_button = FakeUIAItem(
        name="Dalej >",
        left=1000,
        top=900,
        width=120,
        height=40,
    )

    root_window = FakeUIAWindow(
        (root_item,),
        title="Okna - WindowHub",
    )
    dialog_window = FakeUIAWindow(
        (dialog_button,),
        title="Wielkość okna",
    )
    desktop = FakeDesktop(
        root_window,
        windows_by_handle={
            200: root_window,
            400: dialog_window,
        },
    )

    observation = make_observation()
    observation.metadata["window_handle"] = 200
    observation.metadata["foreground_window_handle"] = 400
    observation.metadata["foreground_root_owner_handle"] = 200

    elements = WindowHubUIAutomationProvider(
        desktop_factory=lambda: desktop,
    ).perceive(observation)

    labels = {element.label for element in elements}
    assert "Dodaj" in labels
    assert "Dalej >" in labels
