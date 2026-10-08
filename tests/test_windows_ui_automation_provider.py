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
from app.agent.perception.windows_ui_automation_provider import (
    WindowsUIAutomationProvider,
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
        height=40,
        runtime_id=(1, 2, 3),
        value=None,
    ):
        self.element_info = SimpleNamespace(
            name=name,
            control_type=control_type,
            automation_id=automation_id,
            enabled=enabled,
            visible=visible,
            runtime_id=runtime_id,
            rich_text=value,
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
    def __init__(
        self,
        items,
        title="Visual Studio Code",
    ):
        self._items = tuple(items)
        self._title = title

    def window_text(self):
        return self._title

    def descendants(self):
        return self._items


class FakeDesktop:
    def __init__(
        self,
        windows_by_handle,
    ):
        self._windows = dict(windows_by_handle)

    def window(self, *, handle):
        return self._windows[handle]


def make_observation():
    return EnvironmentObservation(
        state=EnvironmentState(
            active_application="WindowsDesktop",
            active_window_title="Visual Studio Code",
        ),
        metadata={
            "window_rect": SimpleNamespace(
                left=100,
                top=200,
                width=1200,
                height=800,
            ),
            "window_handle": 200,
            "foreground_window_handle": 200,
            "foreground_root_owner_handle": 200,
        },
    )


def test_windows_uia_exposes_button_semantics():
    item = FakeUIAItem(
        name="Zapisz",
        automation_id="save",
    )

    window = FakeUIAWindow(
        (item,),
        title="Visual Studio Code",
    )

    desktop = FakeDesktop(
        {200: window}
    )

    elements = WindowsUIAutomationProvider(
        desktop_factory=lambda: desktop,
    ).perceive(
        make_observation()
    )

    assert len(elements) == 1

    element = elements[0]

    assert element.label == "Zapisz"
    assert element.kind == "button"
    assert (
        element.interaction_capability
        is InteractionCapability.CLICKABLE
    )
    assert element.x == 20
    assert element.y == 20
    assert element.width == 100
    assert element.height == 40
    assert element.metadata["source"] == (
        "windows_ui_automation"
    )
    assert element.metadata["uia_runtime_id"] == (
        "1-2-3"
    )


def test_windows_uia_exposes_editor_value():
    item = FakeUIAItem(
        name="Nazwa",
        control_type="Edit",
        value="Test dokumentu",
    )

    window = FakeUIAWindow(
        (item,),
        title="Visual Studio Code",
    )

    desktop = FakeDesktop(
        {200: window}
    )

    elements = WindowsUIAutomationProvider(
        desktop_factory=lambda: desktop,
    ).perceive(
        make_observation()
    )

    assert len(elements) == 1
    assert elements[0].kind == "edit"
    assert elements[0].metadata["current_value"] == (
        "Test dokumentu"
    )


def test_windows_uia_uses_text_neighbor_for_unlabelled_editor():
    label = FakeUIAItem(
        name="Nazwa pliku",
        control_type="Text",
        left=110,
        top=220,
        width=100,
        height=24,
    )

    editor = FakeUIAItem(
        name="",
        control_type="Edit",
        left=230,
        top=220,
        width=200,
        height=30,
    )

    window = FakeUIAWindow(
        (label, editor),
        title="Visual Studio Code",
    )

    desktop = FakeDesktop(
        {200: window}
    )

    elements = WindowsUIAutomationProvider(
        desktop_factory=lambda: desktop,
    ).perceive(
        make_observation()
    )

    assert len(elements) == 1
    assert elements[0].label == "Nazwa pliku"


def test_windows_uia_rejects_unlabelled_interactive_control():
    item = FakeUIAItem(
        name="",
        control_type="Button",
        automation_id="IDC_BUTTON_1",
    )

    window = FakeUIAWindow(
        (item,),
        title="Visual Studio Code",
    )

    desktop = FakeDesktop(
        {200: window}
    )

    elements = WindowsUIAutomationProvider(
        desktop_factory=lambda: desktop,
    ).perceive(
        make_observation()
    )

    assert elements == ()
