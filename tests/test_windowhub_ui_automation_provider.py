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
        handle=None,
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
            handle=handle,
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


class FakeSelectedUIAItem(FakeUIAItem):
    def is_selected(self):
        return True


class FakeMdiChild(FakeUIAItem):
    def __init__(self, *, name, parent, descendants, **kwargs):
        super().__init__(
            name=name,
            control_type="Window",
            class_name="Afx:MDIChild",
            parent=parent,
            **kwargs,
        )
        self._descendants = tuple(descendants)

    def descendants(self):
        return self._descendants


class FakeGridCell:
    def __init__(
        self,
        *,
        name,
        value,
        left,
        top,
        width=80,
        height=24,
        offscreen=False,
    ):
        self.CurrentName = name
        self.CurrentIsOffscreen = offscreen
        self.CurrentBoundingRectangle = SimpleNamespace(
            left=left,
            top=top,
            right=left + width,
            bottom=top + height,
        )
        self.patterns = {
            "LegacyIAccessible": SimpleNamespace(
                CurrentName=name,
                CurrentValue=value,
            ),
        }
        if value is not None:
            self.patterns["Value"] = SimpleNamespace(
                CurrentValue=value,
                CurrentIsReadOnly=True,
            )


class FakeGridPattern:
    def __init__(self, rows, columns, cells):
        self.CurrentRowCount = rows
        self.CurrentColumnCount = columns
        self._cells = tuple(cells)

    def GetItem(self, row, column):
        return self._cells[row * self.CurrentColumnCount + column]


class FakeUIAGrid(FakeUIAItem):
    def __init__(self, *, parent, rows, columns, cells):
        super().__init__(
            name="",
            control_type="DataGrid",
            class_name="DataGrid",
            parent=parent,
            left=100,
            top=200,
            width=300,
            height=120,
        )
        self.iface_grid = FakeGridPattern(rows, columns, cells)


def make_observation(tracked_objects=(), *, title="Okna - WindowHub"):
    return EnvironmentObservation(
        state=EnvironmentState(
            active_window_title=title,
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


def test_ui_automation_provider_records_native_handle_separately_from_enumeration_window():
    item = FakeUIAItem(
        name="Typ pakietu szybowego",
        control_type="ComboBox",
        handle=701,
    )
    window = FakeUIAWindow(
        (item,),
        title="Okna - OFR/4300-",
    )
    observation = make_observation(title="Okna - OFR/4300-")
    observation.metadata["window_handle"] = 200
    desktop = FakeDesktop(
        window,
        windows_by_handle={200: window},
    )

    elements = WindowHubUIAutomationProvider(
        desktop_factory=lambda: desktop,
    ).perceive(observation)

    assert len(elements) == 1
    metadata = elements[0].metadata
    assert metadata["uia_window_handle"] == 200
    assert metadata["uia_native_handle"] == 701


def test_ui_automation_provider_exposes_mdi_grid_cells_as_read_only_observations():
    mdi_client = FakeUIAItem(
        name="",
        control_type="Pane",
        class_name="MDIClient",
        left=100,
        top=200,
        width=900,
        height=700,
    )
    tab_host = FakeUIAItem(
        name="",
        control_type="Tab",
        class_name="Afx:TabWnd",
        parent=mdi_client,
    )
    document_tab = FakeSelectedUIAItem(
        name="OFR/4024",
        control_type="TabItem",
        parent=tab_host,
    )
    cells = [
        FakeGridCell(
            name="Szerokość",
            value="1230",
            left=110,
            top=220,
        ),
        FakeGridCell(
            name="Opis",
            value="",
            left=195,
            top=220,
        ),
        FakeGridCell(
            name="Poza widokiem",
            value="ignored",
            left=500,
            top=500,
            offscreen=True,
        ),
    ]
    grid = FakeUIAGrid(
        parent=None,
        rows=1,
        columns=3,
        cells=cells,
    )
    child = FakeMdiChild(
        name="OFR/4024",
        parent=mdi_client,
        descendants=(grid,),
    )
    grid._parent = child

    root = FakeUIAWindow(
        (mdi_client, tab_host, document_tab, child, grid),
        title="Okna - WindowHub",
    )
    desktop = FakeDesktop(root)

    def pattern_getter(cell, pattern_name):
        return cell.patterns[pattern_name]

    elements = WindowHubUIAutomationProvider(
        desktop_factory=lambda: desktop,
        pattern_interface_getter=pattern_getter,
    ).perceive(make_observation())

    grid_cells = tuple(
        element for element in elements
        if element.kind == "gridcell"
    )

    assert len(grid_cells) == 2
    first, blank = grid_cells
    assert first.label == "Szerokość"
    assert first.metadata["current_value"] == "1230"
    assert first.metadata["current_value_available"] is True
    assert first.metadata["document_scope"] == "OFR/4024"
    assert first.metadata["uia_grid_row_index"] == 0
    assert first.metadata["uia_grid_column_index"] == 0
    assert first.interaction_capability is InteractionCapability.UNKNOWN
    assert first.metadata["uia_grid_cell_observation"] is True
    assert "tracked_object_id" not in first.metadata

    assert blank.label == "Opis"
    assert blank.metadata["current_value"] == ""
    assert blank.metadata["current_value_available"] is True
    assert blank.metadata["uia_grid_column_index"] == 1


def test_grid_cell_offscreen_hint_does_not_override_intersecting_grid_viewport():
    mdi_client = FakeUIAItem(
        name="",
        control_type="Pane",
        class_name="MDIClient",
        left=100,
        top=200,
        width=900,
        height=700,
    )
    tab_host = FakeUIAItem(
        name="",
        control_type="Tab",
        class_name="Afx:TabWnd",
        parent=mdi_client,
    )
    document_tab = FakeSelectedUIAItem(
        name="OFR/4024",
        control_type="TabItem",
        parent=tab_host,
    )
    # UIA reports this realized cell as offscreen, but its bounds are inside
    # the grid viewport. Geometry and the unique MDI/document match govern.
    cell = FakeGridCell(
        name="Width",
        value="1230",
        left=110,
        top=220,
        offscreen=True,
    )
    grid = FakeUIAGrid(
        parent=None,
        rows=1,
        columns=1,
        cells=(cell,),
    )
    child = FakeMdiChild(
        name="OFR/4024",
        parent=mdi_client,
        descendants=(grid,),
    )
    grid._parent = child
    root = FakeUIAWindow(
        (mdi_client, tab_host, document_tab, child, grid),
        title="Okna - WindowHub",
    )

    def pattern_getter(item, pattern_name):
        return item.patterns[pattern_name]

    elements = WindowHubUIAutomationProvider(
        desktop_factory=lambda: FakeDesktop(root),
        pattern_interface_getter=pattern_getter,
    ).perceive(make_observation())

    cells = tuple(element for element in elements if element.kind == "gridcell")
    assert len(cells) == 1
    assert cells[0].metadata["uia_grid_cell_observation"] is True
    assert cells[0].metadata["uia_grid_cell_offscreen_hint"] is True
    assert cells[0].metadata["document_scope"] == "OFR/4024"


def test_grid_cell_uses_matched_mdi_document_bounds_not_grid_wrapper_bounds():
    mdi_client = FakeUIAItem(
        name="",
        control_type="Pane",
        class_name="MDIClient",
        left=100,
        top=200,
        width=900,
        height=700,
    )
    tab_host = FakeUIAItem(
        name="",
        control_type="Tab",
        class_name="Afx:TabWnd",
        parent=mdi_client,
    )
    document_tab = FakeSelectedUIAItem(
        name="OFR/4024",
        control_type="TabItem",
        parent=tab_host,
    )
    cell = FakeGridCell(
        name="Width",
        value="1230",
        left=400,
        top=300,
        offscreen=True,
    )
    grid = FakeUIAGrid(
        parent=None,
        rows=1,
        columns=1,
        cells=(cell,),
    )
    # Simulate a stale/small DataGrid wrapper rectangle while the cell
    # returned by GridPattern is inside the matched document and MDIClient.
    grid._rectangle = SimpleNamespace(
        left=100,
        top=200,
        width=lambda: 20,
        height=lambda: 20,
    )
    child = FakeMdiChild(
        name="OFR/4024",
        parent=mdi_client,
        descendants=(grid,),
        left=100,
        top=200,
        width=600,
        height=500,
    )
    grid._parent = child
    root = FakeUIAWindow(
        (mdi_client, tab_host, document_tab, child, grid),
        title="Okna - WindowHub",
    )

    def pattern_getter(item, pattern_name):
        return item.patterns[pattern_name]

    elements = WindowHubUIAutomationProvider(
        desktop_factory=lambda: FakeDesktop(root),
        pattern_interface_getter=pattern_getter,
    ).perceive(make_observation())

    cells = tuple(element for element in elements if element.kind == "gridcell")
    assert len(cells) == 1
    assert cells[0].metadata["document_scope"] == "OFR/4024"
    assert cells[0].metadata["uia_grid_cell_offscreen_hint"] is True


def test_ui_automation_provider_fails_closed_for_ambiguous_mdi_document_captions():
    mdi_client = FakeUIAItem(
        name="",
        control_type="Pane",
        class_name="MDIClient",
        left=100,
        top=200,
        width=900,
        height=700,
    )
    tab_host = FakeUIAItem(
        name="",
        control_type="Tab",
        class_name="Afx:TabWnd",
        parent=mdi_client,
    )
    tab_a = FakeSelectedUIAItem(
        name="OFR/4024",
        control_type="TabItem",
        parent=tab_host,
    )
    tab_b = FakeUIAItem(
        name="OFR/4024",
        control_type="TabItem",
        parent=tab_host,
    )

    grid_a = FakeUIAGrid(
        parent=None,
        rows=1,
        columns=1,
        cells=[FakeGridCell(name="Cell A", value="A", left=110, top=220)],
    )
    child_a = FakeMdiChild(
        name="OFR/4024",
        parent=mdi_client,
        descendants=(grid_a,),
    )
    grid_a._parent = child_a

    grid_b = FakeUIAGrid(
        parent=None,
        rows=1,
        columns=1,
        cells=[FakeGridCell(name="Cell B", value="B", left=110, top=250)],
    )
    child_b = FakeMdiChild(
        name="OFR/4024",
        parent=mdi_client,
        descendants=(grid_b,),
    )
    grid_b._parent = child_b

    root = FakeUIAWindow(
        (
            mdi_client,
            tab_host,
            tab_a,
            tab_b,
            child_a,
            grid_a,
            child_b,
            grid_b,
        ),
        title="Okna - WindowHub",
    )

    def pattern_getter(cell, pattern_name):
        return cell.patterns[pattern_name]

    elements = WindowHubUIAutomationProvider(
        desktop_factory=lambda: FakeDesktop(root),
        pattern_interface_getter=pattern_getter,
    ).perceive(make_observation())

    assert not any(
        element.kind == "gridcell"
        for element in elements
    )


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


def test_ui_automation_provider_resolves_scope_from_uniquely_matched_mdi_child():
    mdi_client = FakeUIAItem(
        name="",
        control_type="Pane",
        class_name="MDIClient",
    )
    tab_host = FakeUIAItem(
        name="",
        control_type="Tab",
        class_name="Afx:TabWnd",
        parent=mdi_client,
    )
    document_tab = FakeSelectedUIAItem(
        name="Start1",
        control_type="TabItem",
        parent=tab_host,
    )
    child = FakeMdiChild(
        name="Start1",
        parent=mdi_client,
        descendants=(),
        handle=501,
    )
    button = FakeUIAItem(
        name="NOWA OFERTA",
        control_type="Button",
        automation_id="Nowa_oferta",
        parent=child,
    )
    child._descendants = (button,)
    root = FakeUIAWindow(
        (mdi_client, tab_host, document_tab, child, button),
        title="Okna - OFR/4456-",
    )

    elements = WindowHubUIAutomationProvider(
        desktop_factory=lambda: FakeDesktop(root),
    ).perceive(make_observation(title="Okna - OFR/4456-"))

    buttons = tuple(element for element in elements if element.label == "NOWA OFERTA")
    assert len(buttons) == 1
    assert buttons[0].metadata["uia_native_handle"] is None
    assert buttons[0].metadata["document_scope"] == "Start1"


def test_ui_automation_provider_keeps_scope_unknown_for_ambiguous_mdi_child_match():
    mdi_client = FakeUIAItem(
        name="",
        control_type="Pane",
        class_name="MDIClient",
    )
    tab_host = FakeUIAItem(
        name="",
        control_type="Tab",
        class_name="Afx:TabWnd",
        parent=mdi_client,
    )
    tab_a = FakeSelectedUIAItem(
        name="Start1",
        control_type="TabItem",
        parent=tab_host,
    )
    tab_b = FakeUIAItem(
        name="Start1",
        control_type="TabItem",
        parent=tab_host,
    )
    child_a = FakeMdiChild(
        name="Start1",
        parent=mdi_client,
        descendants=(),
        handle=501,
    )
    child_b = FakeMdiChild(
        name="Start1",
        parent=mdi_client,
        descendants=(),
        handle=502,
    )
    button = FakeUIAItem(
        name="NOWA OFERTA",
        control_type="Button",
        automation_id="Nowa_oferta",
        parent=child_a,
    )
    child_a._descendants = (button,)
    root = FakeUIAWindow(
        (mdi_client, tab_host, tab_a, tab_b, child_a, child_b, button),
        title="Okna - OFR/4456-",
    )

    elements = WindowHubUIAutomationProvider(
        desktop_factory=lambda: FakeDesktop(root),
    ).perceive(make_observation(title="Okna - OFR/4456-"))

    buttons = tuple(element for element in elements if element.label == "NOWA OFERTA")
    assert len(buttons) == 1
    assert buttons[0].metadata["document_scope"] is None


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
        handle=501,
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
        ("Pane", "Afx:Pane", "Konstrukcja", 501),
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


def test_target_resolver_prefers_unique_nested_tab_on_label_collision():
    button = ScreenElement(
        kind="button",
        label="W?a?ciwo?ci",
        metadata={
            "source": "windowhub_ui_automation",
            "uia_tab_scope": None,
        },
    )

    nested_tab = ScreenElement(
        kind="tabitem",
        label="W?a?ciwo?ci",
        metadata={
            "source": "windowhub_ui_automation",
            "uia_tab_scope": "nested",
            "uia_selected": True,
        },
    )

    scene = __import__(
        "app.agent.perception.screen_scene",
        fromlist=["ScreenScene"],
    ).ScreenScene(
        observation=None,
        elements=(button, nested_tab),
        metadata={
            "active_document": "Dokument5",
        },
    )

    resolution = TargetResolver().resolve(
        scene,
        "W?a?ciwo?ci",
    )

    assert resolution.resolved is True
    assert resolution.element is nested_tab
    assert resolution.score == 1.0
    assert "nested UIA tab" in resolution.reason
