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
        class_name=None,
        parent=None,
        selected=None,
    ):
        self.element_info = SimpleNamespace(
            name=name,
            control_type=control_type,
            class_name=class_name or control_type,
            automation_id=automation_id,
            enabled=enabled,
            visible=visible,
            runtime_id=runtime_id,
            rich_text=value,
        )
        self._parent = parent
        self._selected = selected

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

    def is_selected(self):
        if self._selected is None:
            raise RuntimeError("Selection state not supported by this fake item.")
        return self._selected


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



def test_windows_uia_classifies_document_tab_by_mdi_ancestry():
    mdi_client = FakeUIAItem(
        name="",
        control_type="Pane",
        class_name="MDIClient",
        width=1200,
        height=800,
        runtime_id=(10,),
    )
    document_tab = FakeUIAItem(
        name="",
        control_type="Tab",
        class_name="Afx:TabWnd:6e0000:8:10003:10",
        parent=mdi_client,
        width=500,
        height=24,
        runtime_id=(11,),
    )
    tab_item = FakeUIAItem(
        name="OFR/4330- <>",
        control_type="TabItem",
        parent=document_tab,
        selected=True,
        left=130,
        top=205,
        width=124,
        height=21,
        runtime_id=(12,),
    )
    application_tab_container = FakeUIAItem(
        name="",
        control_type="Tab",
        class_name="SysTabControl32",
        parent=FakeUIAItem(
            name="",
            control_type="Pane",
            class_name="Afx:ControlBar:6e0000:8:10003:10",
            width=1200,
            height=100,
            runtime_id=(20,),
        ),
        width=1200,
        height=30,
        runtime_id=(21,),
    )
    panel_tab = FakeUIAItem(
        name="Notatka",
        control_type="TabItem",
        parent=application_tab_container,
        selected=True,
        left=130,
        top=240,
        width=61,
        height=21,
        runtime_id=(22,),
    )

    window = FakeUIAWindow(
        (tab_item, panel_tab),
        title="Visual Studio Code",
    )
    desktop = FakeDesktop({200: window})
    elements = WindowsUIAutomationProvider(
        desktop_factory=lambda: desktop,
    ).perceive(make_observation())

    document_element = next(
        element for element in elements
        if element.label == "OFR/4330- <>"
    )
    panel_element = next(
        element for element in elements
        if element.label == "Notatka"
    )

    assert document_element.metadata["uia_tab_scope"] == "document"
    assert document_element.metadata["uia_document_tab_selected"] is True
    assert panel_element.metadata["uia_tab_scope"] == "application"
    assert "uia_document_tab_selected" not in panel_element.metadata


def test_windows_uia_leaves_unknown_tab_ancestry_unclassified():
    unknown_tab = FakeUIAItem(
        name="Unknown",
        control_type="TabItem",
        selected=True,
        runtime_id=(31,),
    )
    window = FakeUIAWindow(
        (unknown_tab,),
        title="Visual Studio Code",
    )
    desktop = FakeDesktop({200: window})

    elements = WindowsUIAutomationProvider(
        desktop_factory=lambda: desktop,
    ).perceive(make_observation())

    assert len(elements) == 1
    assert "uia_tab_scope" not in elements[0].metadata
    assert "uia_document_tab_selected" not in elements[0].metadata


def test_active_document_resolution_ignores_selected_application_tabs():
    from app.agent.perception.perception_engine import PerceptionEngine

    document_tab = FakeUIAItem(
        name="Offer A",
        control_type="TabItem",
        parent=FakeUIAItem(
            name="",
            control_type="Tab",
            class_name="Afx:TabWnd:abc",
            parent=FakeUIAItem(
                name="",
                control_type="Pane",
                class_name="MDIClient",
            ),
        ),
        selected=True,
        runtime_id=(41,),
    )
    selected_panel_tab = FakeUIAItem(
        name="Notatka",
        control_type="TabItem",
        parent=FakeUIAItem(
            name="",
            control_type="Tab",
            class_name="SysTabControl32",
            parent=FakeUIAItem(
                name="",
                control_type="Pane",
                class_name="Afx:ControlBar:abc",
            ),
        ),
        selected=True,
        runtime_id=(42,),
        top=270,
    )
    window = FakeUIAWindow(
        (document_tab, selected_panel_tab),
        title="Visual Studio Code",
    )
    desktop = FakeDesktop({200: window})
    elements = WindowsUIAutomationProvider(
        desktop_factory=lambda: desktop,
    ).perceive(make_observation())

    active_document, document_count, selected_count = (
        PerceptionEngine._resolve_active_document(elements)
    )

    assert active_document == "Offer A"
    assert document_count == 1
    assert selected_count == 1
