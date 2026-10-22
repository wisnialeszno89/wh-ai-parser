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


class FakeMDIChildWindow(FakeUIAItem):
    """Fake MDI child with an independently enumerated descendant subtree."""

    def __init__(self, items, **kwargs):
        super().__init__(**kwargs)
        self._descendant_items = tuple(items)

    def descendants(self):
        return self._descendant_items


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



def make_mdi_tab(name, mdi_client, *, selected, runtime_id):
    tab_host = FakeUIAItem(
        name="",
        control_type="Tab",
        class_name="Afx:TabWnd:6e0000:8:10003:10",
        parent=mdi_client,
        width=500,
        height=24,
        runtime_id=(runtime_id, 1),
    )
    return FakeUIAItem(
        name=name,
        control_type="TabItem",
        parent=tab_host,
        selected=selected,
        left=130,
        top=205,
        width=124,
        height=21,
        runtime_id=(runtime_id, 2),
    )


def test_windows_uia_assigns_document_scope_by_unique_mdi_tab_caption_match():
    from app.agent.perception.perception_engine import PerceptionEngine

    mdi_client = FakeUIAItem(
        name="",
        control_type="Pane",
        class_name="MDIClient",
        width=1200,
        height=800,
        runtime_id=(50,),
    )
    document_tab = make_mdi_tab(
        "OFR/4330- <>",
        mdi_client,
        selected=True,
        runtime_id=51,
    )
    document_window = FakeUIAItem(
        name="OFR/4330- <>",
        control_type="Window",
        class_name="Afx:006E0000:b:00010003:00000006:2C912341",
        parent=mdi_client,
        width=1100,
        height=700,
        runtime_id=(52,),
    )
    document_pane = FakeUIAItem(
        name="",
        control_type="Pane",
        class_name="DocumentForm",
        parent=document_window,
        width=700,
        height=500,
        runtime_id=(53,),
    )
    document_button = FakeUIAItem(
        name="Dodaj artykuł do konstrukcji",
        control_type="Button",
        parent=document_pane,
        runtime_id=(54,),
    )

    home_window = FakeUIAItem(
        name="Start1",
        control_type="Window",
        class_name="Afx:006E0000:b:00010003:00000006:12345678",
        parent=mdi_client,
        width=1100,
        height=700,
        runtime_id=(55,),
    )
    home_button = FakeUIAItem(
        name="NOWA OFERTA",
        control_type="Button",
        parent=home_window,
        runtime_id=(56,),
    )

    window = FakeUIAWindow(
        (
            mdi_client,
            document_tab.parent(),
            document_tab,
            document_window,
            document_pane,
            document_button,
            home_window,
            home_button,
        ),
        title="Visual Studio Code",
    )
    desktop = FakeDesktop({200: window})
    elements = WindowsUIAutomationProvider(
        desktop_factory=lambda: desktop,
    ).perceive(make_observation())

    observed_document_button = next(
        element for element in elements
        if element.label == "Dodaj artykuł do konstrukcji"
    )
    observed_home_button = next(
        element for element in elements
        if element.label == "NOWA OFERTA"
    )
    observed_document_tab = next(
        element for element in elements
        if element.label == "OFR/4330- <>"
    )

    assert observed_document_button.metadata["document_scope"] == "OFR/4330- <>"
    assert "document_scope" not in observed_home_button.metadata
    assert observed_document_tab.metadata["uia_tab_scope"] == "document"

    active_document, document_count, selected_count = (
        PerceptionEngine._resolve_active_document(elements)
    )
    assert active_document == "OFR/4330- <>"
    assert document_count == 1
    assert selected_count == 1


def test_windows_uia_scopes_wpf_descendant_by_runtime_id_when_parent_chain_stops():
    mdi_client = FakeUIAItem(
        name="",
        control_type="Pane",
        class_name="MDIClient",
        width=1200,
        height=800,
        runtime_id=(80,),
    )
    document_tab = make_mdi_tab(
        "Offer A",
        mdi_client,
        selected=True,
        runtime_id=81,
    )

    # Simulate a WPF content boundary: descendants are enumerable beneath
    # the MDI child, but the wrapper parent chain ends at the Expander.
    expander = FakeUIAItem(
        name="",
        control_type="Group",
        class_name="Expander",
        runtime_id=(82,),
    )
    document_button = FakeUIAItem(
        name="Add to offer",
        control_type="Button",
        parent=expander,
        runtime_id=(83,),
    )
    document_window = FakeMDIChildWindow(
        (expander, document_button),
        name="Offer A",
        control_type="Window",
        class_name="Afx:MDIChild",
        parent=mdi_client,
        width=1100,
        height=700,
        runtime_id=(84,),
    )

    home_button = FakeUIAItem(
        name="New offer",
        control_type="Button",
        runtime_id=(85,),
    )
    window = FakeUIAWindow(
        (
            mdi_client,
            document_tab.parent(),
            document_tab,
            document_window,
            expander,
            document_button,
            home_button,
        ),
        title="Visual Studio Code",
    )
    desktop = FakeDesktop({200: window})
    elements = WindowsUIAutomationProvider(
        desktop_factory=lambda: desktop,
    ).perceive(make_observation())

    observed_document_button = next(
        element for element in elements
        if element.label == "Add to offer"
    )
    observed_home_button = next(
        element for element in elements
        if element.label == "New offer"
    )

    assert observed_document_button.metadata["document_scope"] == "Offer A"
    assert "document_scope" not in observed_home_button.metadata


def test_windows_uia_leaves_runtime_id_unscoped_when_shared_across_documents():
    mdi_client = FakeUIAItem(
        name="",
        control_type="Pane",
        class_name="MDIClient",
        width=1200,
        height=800,
        runtime_id=(90,),
    )
    tab_a = make_mdi_tab(
        "Offer A", mdi_client, selected=True, runtime_id=91
    )
    tab_b = make_mdi_tab(
        "Offer B", mdi_client, selected=False, runtime_id=92
    )

    expander_a = FakeUIAItem(
        name="", control_type="Group", class_name="Expander", runtime_id=(93,)
    )
    button_a = FakeUIAItem(
        name="Add A", control_type="Button", parent=expander_a,
        runtime_id=(999,),
    )
    child_a = FakeMDIChildWindow(
        (expander_a, button_a),
        name="Offer A", control_type="Window", class_name="Afx:MDIChild",
        parent=mdi_client, width=1100, height=700, runtime_id=(94,),
    )

    expander_b = FakeUIAItem(
        name="", control_type="Group", class_name="Expander", runtime_id=(95,)
    )
    button_b = FakeUIAItem(
        name="Add B", control_type="Button", parent=expander_b,
        runtime_id=(999,),
    )
    child_b = FakeMDIChildWindow(
        (expander_b, button_b),
        name="Offer B", control_type="Window", class_name="Afx:MDIChild",
        parent=mdi_client, width=1100, height=700, runtime_id=(96,),
    )

    window = FakeUIAWindow(
        (
            mdi_client,
            tab_a.parent(), tab_a,
            tab_b.parent(), tab_b,
            child_a, expander_a, button_a,
            child_b, expander_b, button_b,
        ),
        title="Visual Studio Code",
    )
    desktop = FakeDesktop({200: window})
    elements = WindowsUIAutomationProvider(
        desktop_factory=lambda: desktop,
    ).perceive(make_observation())

    observed_a = next(element for element in elements if element.label == "Add A")
    observed_b = next(element for element in elements if element.label == "Add B")

    assert "document_scope" not in observed_a.metadata
    assert "document_scope" not in observed_b.metadata


def test_windows_uia_leaves_mdi_children_unscoped_when_caption_does_not_match_tab():
    mdi_client = FakeUIAItem(
        name="",
        control_type="Pane",
        class_name="MDIClient",
        width=1200,
        height=800,
        runtime_id=(60,),
    )
    document_tab = make_mdi_tab(
        "Offer A",
        mdi_client,
        selected=True,
        runtime_id=61,
    )
    document_window = FakeUIAItem(
        name="Offer B",
        control_type="Window",
        class_name="Afx:MDIChild",
        parent=mdi_client,
        width=1100,
        height=700,
        runtime_id=(62,),
    )
    button = FakeUIAItem(
        name="Add",
        control_type="Button",
        parent=document_window,
        runtime_id=(63,),
    )
    window = FakeUIAWindow(
        (mdi_client, document_tab.parent(), document_tab, document_window, button),
        title="Visual Studio Code",
    )
    elements = WindowsUIAutomationProvider(
        desktop_factory=lambda: FakeDesktop({200: window}),
    ).perceive(make_observation())

    observed_button = next(element for element in elements if element.label == "Add")
    assert "document_scope" not in observed_button.metadata


def test_windows_uia_leaves_mdi_children_unscoped_when_tab_caption_is_ambiguous():
    mdi_client = FakeUIAItem(
        name="",
        control_type="Pane",
        class_name="MDIClient",
        width=1200,
        height=800,
        runtime_id=(70,),
    )
    tab1 = make_mdi_tab(
        "Offer A",
        mdi_client,
        selected=True,
        runtime_id=71,
    )
    tab2 = make_mdi_tab(
        "Offer A",
        mdi_client,
        selected=False,
        runtime_id=72,
    )
    child = FakeUIAItem(
        name="Offer A",
        control_type="Window",
        class_name="Afx:MDIChild",
        parent=mdi_client,
        width=1100,
        height=700,
        runtime_id=(73,),
    )
    button = FakeUIAItem(
        name="Add",
        control_type="Button",
        parent=child,
        runtime_id=(74,),
    )
    window = FakeUIAWindow(
        (
            mdi_client, tab1.parent(), tab1, tab2.parent(), tab2,
            child, button,
        ),
        title="Visual Studio Code",
    )
    elements = WindowsUIAutomationProvider(
        desktop_factory=lambda: FakeDesktop({200: window}),
    ).perceive(make_observation())

    observed_button = next(element for element in elements if element.label == "Add")
    assert "document_scope" not in observed_button.metadata
