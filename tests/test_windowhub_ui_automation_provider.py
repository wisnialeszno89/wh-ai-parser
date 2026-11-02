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
from app.agent.perception.screen_scene import (
    ScreenScene,
)
from app.agent.perception.target_resolver import (
    TargetResolver,
)
from app.agent.perception.windowhub_ui_automation_provider import (
    WindowHubUIAutomationProvider,
)
from app.agent.runtime.windowhub_lookup_grid_adapter import (
    WindowHubLookupGridAdapter,
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


def test_ui_automation_provider_exposes_datagrid_as_noninteractive_table():
    lookup = FakeUIAItem(
        name="Zamawiający",
        control_type="Button",
        automation_id="IDC_ZAMAWIAJACY",
    )
    grid = FakeUIAItem(
        name="",
        control_type="DataGrid",
        automation_id="PART_GridControl",
        parent=lookup,
        runtime_id=(7, 18708, 63003992),
    )
    desktop = FakeDesktop(FakeUIAWindow((lookup, grid)))

    elements = WindowHubUIAutomationProvider(
        desktop_factory=lambda: desktop,
    ).perceive(make_observation())

    tables = tuple(element for element in elements if element.kind == "table")
    assert len(tables) == 1
    table = tables[0]
    assert table.label == "Zamawiający"
    assert table.interaction_capability is InteractionCapability.NOT_INTERACTIVE
    assert table.metadata["uia_control_type"] == "datagrid"
    assert table.metadata["uia_runtime_id"] == "7-18708-63003992"
    assert table.metadata["current_value"] is None


def test_ui_automation_provider_uses_generic_label_when_datagrid_has_no_context():
    grid = FakeUIAItem(
        name="",
        control_type="DataGrid",
        automation_id="PART_GridControl",
        runtime_id=(7, 10, 20),
    )
    desktop = FakeDesktop(FakeUIAWindow((grid,)))

    elements = WindowHubUIAutomationProvider(
        desktop_factory=lambda: desktop,
    ).perceive(make_observation())

    tables = tuple(element for element in elements if element.kind == "table")
    assert len(tables) == 1
    assert tables[0].label == "Tabela danych"
    assert tables[0].metadata["semantic_label_source"] == "uia_control_type"
    assert tables[0].interaction_capability is InteractionCapability.NOT_INTERACTIVE


def test_ui_automation_provider_resolves_table_again_from_current_window():
    original = FakeUIAItem(
        name="Zamawiający",
        control_type="DataGrid",
        runtime_id=(7, 10, 20),
    )
    original_desktop = FakeDesktop(FakeUIAWindow((original,)))
    provider = WindowHubUIAutomationProvider(
        desktop_factory=lambda: original_desktop,
    )
    table = next(
        element
        for element in provider.perceive(make_observation())
        if element.kind == "table"
    )

    current = FakeUIAItem(
        name="Zamawiający",
        control_type="DataGrid",
        runtime_id=(7, 10, 20),
    )
    current_desktop = FakeDesktop(FakeUIAWindow((current,)))
    current_provider = WindowHubUIAutomationProvider(
        desktop_factory=lambda: current_desktop,
    )

    resolved = current_provider.resolve_table_element(
        table,
        make_observation(),
    )
    assert resolved is current


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



def test_ui_automation_provider_preserves_lookupedit_ancestor_structure():
    lookup = FakeUIAItem(
        name="Zamawiający",
        control_type="Custom",
        automation_id="IDC_ZAMAWIAJACY",
        class_name="lookupedit",
    )
    grid = FakeUIAItem(
        name="",
        control_type="DataGrid",
        automation_id="PART_GridControl",
        parent=lookup,
        runtime_id=(7, 18708, 63003992),
    )
    desktop = FakeDesktop(FakeUIAWindow((lookup, grid)))

    elements = WindowHubUIAutomationProvider(
        desktop_factory=lambda: desktop,
    ).perceive(make_observation())

    tables = tuple(element for element in elements if element.kind == "table")
    assert len(tables) == 1
    ancestry = tables[0].metadata["uia_ancestor_structure"]
    assert ancestry == (
        {
            "control_type": "custom",
            "class_name": "lookupedit",
            "automation_id": "idc_zamawiajacy",
        },
    )


class _StructureOnlyUIAInfo:
    def __init__(
        self,
        *,
        control_type,
        automation_id="",
        class_name="",
        runtime_id=(9, 8, 7),
        visible=True,
    ):
        self.control_type = control_type
        self.automation_id = automation_id
        self.class_name = class_name
        self.runtime_id = runtime_id
        self.visible = visible

    @property
    def name(self):
        raise AssertionError("Structure-only perception must not read UIA names")

    @property
    def value(self):
        raise AssertionError("Structure-only perception must not read UIA values")

    @property
    def rich_text(self):
        raise AssertionError("Structure-only perception must not read UIA rich text")


class _StructureOnlyUIAItem:
    def __init__(
        self,
        *,
        control_type,
        automation_id="",
        class_name="",
        runtime_id=(9, 8, 7),
        parent=None,
    ):
        self.element_info = _StructureOnlyUIAInfo(
            control_type=control_type,
            automation_id=automation_id,
            class_name=class_name,
            runtime_id=runtime_id,
        )
        self._parent = parent
        self._rectangle = SimpleNamespace(
            left=120,
            top=220,
            width=lambda: 420,
            height=lambda: 260,
        )

    def parent(self):
        return self._parent

    def rectangle(self):
        return self._rectangle


class _StructureOnlyUIAWindow:
    def __init__(self, items):
        self._items = tuple(items)

    def descendants(self):
        return self._items

    def window_text(self):
        raise AssertionError("Structure-only perception must not read window title")


class _StructureOnlyDesktop:
    def __init__(self, window=None, *, windows=None):
        self._windows = dict(windows or {})
        if window is not None:
            self._windows.setdefault(991, window)
        self.requested_handles = []

    def window(self, *, handle):
        self.requested_handles.append(handle)
        if handle not in self._windows:
            raise LookupError("unknown fake window handle")
        window = self._windows[handle]
        return SimpleNamespace(wrapper_object=lambda: window)


def _structure_only_observation(*, include_window_handle=True):
    metadata = {
        "window_rect": SimpleNamespace(
            left=100,
            top=200,
            width=1000,
            height=800,
        ),
        "window_root_owner_handle": 991,
    }
    if include_window_handle:
        metadata["window_handle"] = 991
    return EnvironmentObservation(
        state=EnvironmentState(
            active_application="WindowHub",
            active_window_title="Okna - WindowHub",
        ),
        metadata=metadata,
    )


def test_structure_only_perception_never_reads_ui_text_or_values():
    lookup = _StructureOnlyUIAItem(
        control_type="Custom",
        automation_id="IDC_ZAMAWIAJACY",
        class_name="lookupedit",
        runtime_id=(9, 8, 1),
    )
    grid = _StructureOnlyUIAItem(
        control_type="DataGrid",
        automation_id="PART_GridControl",
        runtime_id=(9, 8, 2),
        parent=lookup,
    )
    window = _StructureOnlyUIAWindow((lookup, grid))
    desktop = _StructureOnlyDesktop(window)
    provider = WindowHubUIAutomationProvider(
        desktop_factory=lambda: desktop,
    )
    observation = _structure_only_observation()

    elements = provider.perceive_structure_only(observation)

    assert len(elements) == 1
    table = elements[0]
    assert table.kind == "table"
    assert table.label == "Tabela"
    assert table.x == 20
    assert table.y == 20
    assert table.width == 420
    assert table.height == 260
    assert table.metadata["perception_mode"] == "structure_only"
    assert table.metadata["automation_id"] == "PART_GridControl"
    assert table.metadata["uia_ancestor_structure"] == (
        {
            "control_type": "custom",
            "class_name": "lookupedit",
            "automation_id": "idc_zamawiajacy",
        },
    )
    assert "name" not in table.metadata
    assert "current_value" not in table.metadata
    assert desktop.requested_handles == [991]

    # The exact same structure-only target must survive adapter resolution
    # without asking the current window for its title or the grid for text.
    scene = ScreenScene(
        observation=observation,
        elements=elements,
    )
    adapter = WindowHubLookupGridAdapter(provider=provider)
    resolution = adapter.resolve_scene_target(scene)

    assert resolution.resolved is True
    assert resolution.element is table
    assert adapter.resolve_current_grid(
        table,
        observation,
    ) is grid


def test_structure_only_diagnostics_report_non_table_structure_without_ui_text():
    parent = _StructureOnlyUIAItem(
        control_type="Custom",
        automation_id="IDC_ZAMAWIAJACY",
        class_name="lookupedit",
        runtime_id=(9, 8, 41),
    )
    popup = _StructureOnlyUIAItem(
        control_type="Pane",
        automation_id="PopupRoot",
        class_name="popupcontent",
        runtime_id=(9, 8, 42),
        parent=parent,
    )
    desktop = _StructureOnlyDesktop(
        _StructureOnlyUIAWindow((parent, popup))
    )
    provider = WindowHubUIAutomationProvider(
        desktop_factory=lambda: desktop,
    )
    diagnostics = []

    elements = provider.perceive_structure_only(
        _structure_only_observation(),
        diagnostic_callback=diagnostics.append,
        diagnostic_limit=10,
    )

    assert elements == ()
    element_records = [
        record for record in diagnostics
        if record.get("diagnostic_type") is None
    ]
    assert len(element_records) == 2
    assert element_records[0]["automation_id"] == "IDC_ZAMAWIAJACY"
    assert element_records[1]["control_type"] == "pane"
    assert element_records[1]["class_name"] == "popupcontent"
    assert element_records[1]["ancestor_structure"] == (
        {
            "control_type": "custom",
            "class_name": "lookupedit",
            "automation_id": "idc_zamawiajacy",
        },
    )
    assert any(
        record.get("diagnostic_type") == "root_scan_completed"
        for record in diagnostics
    )
    assert all(
        not ({"name", "value", "text", "current_value"} & set(record))
        for record in diagnostics
    )


def test_structure_only_diagnostics_report_table_candidate_with_unavailable_bounds():
    class NoBoundsGrid(_StructureOnlyUIAItem):
        def rectangle(self):
            raise RuntimeError("bounds unavailable")

    lookup = _StructureOnlyUIAItem(
        control_type="Custom",
        automation_id="IDC_ZAMAWIAJACY",
        class_name="lookupedit",
        runtime_id=(9, 8, 51),
    )
    grid = NoBoundsGrid(
        control_type="DataGrid",
        automation_id="PART_GridControl",
        runtime_id=(9, 8, 52),
        parent=lookup,
    )
    diagnostics = []
    provider = WindowHubUIAutomationProvider(
        desktop_factory=lambda: _StructureOnlyDesktop(
            _StructureOnlyUIAWindow((lookup, grid))
        ),
    )

    elements = provider.perceive_structure_only(
        _structure_only_observation(),
        diagnostic_callback=diagnostics.append,
        diagnostic_limit=10,
    )

    assert elements == ()
    table_records = [
        record for record in diagnostics
        if record.get("candidate_kind") == "table_control"
    ]
    assert len(table_records) == 1
    assert table_records[0]["automation_id"] == "PART_GridControl"
    assert table_records[0]["rejection_reason"] == "rectangle_error"
    assert table_records[0]["rectangle_error_type"] == "RuntimeError"
    assert table_records[0]["ancestor_structure"][0]["automation_id"] == (
        "idc_zamawiajacy"
    )


def test_structure_only_diagnostics_are_bounded():
    items = tuple(
        _StructureOnlyUIAItem(
            control_type="Pane",
            automation_id=f"pane-{index}",
            runtime_id=(9, 9, index + 1),
        )
        for index in range(5)
    )
    provider = WindowHubUIAutomationProvider(
        desktop_factory=lambda: _StructureOnlyDesktop(
            _StructureOnlyUIAWindow(items)
        ),
    )
    diagnostics = []

    provider.perceive_structure_only(
        _structure_only_observation(),
        diagnostic_callback=diagnostics.append,
        diagnostic_limit=2,
    )

    assert len(diagnostics) == 2


def test_structure_only_diagnostic_limit_rejects_invalid_values():
    provider = WindowHubUIAutomationProvider(
        desktop_factory=lambda: _StructureOnlyDesktop(
            _StructureOnlyUIAWindow(())
        ),
    )
    for invalid in (True, -1, 501, 1.5):
        try:
            provider.perceive_structure_only(
                _structure_only_observation(),
                diagnostic_limit=invalid,
            )
        except ValueError as exc:
            assert str(exc) == "uia_structure_only_diagnostic_limit_invalid"
        else:
            raise AssertionError("Invalid diagnostic limit was accepted")


def test_structure_only_perception_requires_explicit_window_handle():
    desktop_factory_calls = []
    provider = WindowHubUIAutomationProvider(
        desktop_factory=lambda: desktop_factory_calls.append(True),
    )

    elements = provider.perceive_structure_only(
        _structure_only_observation(include_window_handle=False)
    )

    assert elements == ()
    assert desktop_factory_calls == []


def test_structure_only_perception_finds_grid_in_windowhub_owned_foreground_popup():
    lookup = _StructureOnlyUIAItem(
        control_type="Custom",
        automation_id="IDC_ZAMAWIAJACY",
        class_name="lookupedit",
        runtime_id=(9, 8, 11),
    )
    grid = _StructureOnlyUIAItem(
        control_type="DataGrid",
        automation_id="PART_GridControl",
        runtime_id=(9, 8, 12),
        parent=lookup,
    )
    main_window = _StructureOnlyUIAWindow(())
    popup_window = _StructureOnlyUIAWindow((lookup, grid))
    desktop = _StructureOnlyDesktop(
        windows={
            991: main_window,
            992: popup_window,
        }
    )
    provider = WindowHubUIAutomationProvider(
        desktop_factory=lambda: desktop,
    )
    observation = _structure_only_observation()
    observation = EnvironmentObservation(
        state=observation.state,
        metadata={
            **observation.metadata,
            "foreground_window_handle": 992,
            "foreground_root_owner_handle": 991,
        },
    )

    elements = provider.perceive_structure_only(observation)

    assert len(elements) == 1
    table = elements[0]
    assert table.metadata["automation_id"] == "PART_GridControl"
    assert table.metadata["uia_root_window_handle"] == 992
    assert desktop.requested_handles == [991, 992]

    scene = ScreenScene(
        observation=observation,
        elements=elements,
    )
    adapter = WindowHubLookupGridAdapter(provider=provider)
    resolution = adapter.resolve_scene_target(scene)

    assert resolution.resolved is True
    assert adapter.resolve_current_grid(table, observation) is grid
    assert desktop.requested_handles[-1] == 992


def test_structure_only_perception_accepts_popup_owned_by_app_root_not_modal_form():
    lookup = _StructureOnlyUIAItem(
        control_type="Custom",
        automation_id="IDC_ZAMAWIAJACY",
        class_name="lookupedit",
        runtime_id=(9, 8, 18),
    )
    grid = _StructureOnlyUIAItem(
        control_type="DataGrid",
        automation_id="PART_GridControl",
        runtime_id=(9, 8, 19),
        parent=lookup,
    )
    desktop = _StructureOnlyDesktop(
        windows={
            991: _StructureOnlyUIAWindow(()),
            992: _StructureOnlyUIAWindow((lookup, grid)),
        }
    )
    provider = WindowHubUIAutomationProvider(
        desktop_factory=lambda: desktop,
    )
    base = _structure_only_observation()
    observation = EnvironmentObservation(
        state=base.state,
        metadata={
            **base.metadata,
            "window_handle": 991,
            "window_root_owner_handle": 990,
            "foreground_window_handle": 992,
            "foreground_root_owner_handle": 990,
        },
    )

    elements = provider.perceive_structure_only(observation)

    assert len(elements) == 1
    assert elements[0].metadata["automation_id"] == "PART_GridControl"
    assert elements[0].metadata["uia_root_window_handle"] == 992
    assert desktop.requested_handles == [991, 992]


def test_structure_only_perception_scans_owned_foreground_popup_before_large_main_tree():
    grid = _StructureOnlyUIAItem(
        control_type="DataGrid",
        automation_id="PART_GridControl",
        runtime_id=(9, 8, 61),
    )
    main_window = _StructureOnlyUIAWindow(())
    popup_window = _StructureOnlyUIAWindow((grid,))
    desktop = _StructureOnlyDesktop(
        windows={991: main_window, 992: popup_window}
    )
    provider = WindowHubUIAutomationProvider(
        desktop_factory=lambda: desktop,
    )
    base = _structure_only_observation()
    observation = EnvironmentObservation(
        state=base.state,
        metadata={
            **base.metadata,
            "foreground_window_handle": 992,
            "foreground_root_owner_handle": 991,
            "window_root_owner_handle": 991,
        },
    )
    diagnostics = []

    elements = provider.perceive_structure_only(
        observation,
        diagnostic_callback=diagnostics.append,
    )

    assert len(elements) == 1
    assert desktop.requested_handles == [992, 991]
    assert diagnostics[0]["diagnostic_type"] == "root_scan_started"
    assert diagnostics[0]["root_window_handle"] == 992
    assert any(
        record.get("diagnostic_type") == "root_scan_completed"
        and record.get("root_window_handle") == 992
        for record in diagnostics
    )


def test_structure_only_perception_reports_root_descendants_errors():
    class BrokenWindow:
        def descendants(self):
            raise RuntimeError("UIA provider unavailable")

    desktop = _StructureOnlyDesktop(
        windows={991: BrokenWindow()}
    )
    provider = WindowHubUIAutomationProvider(
        desktop_factory=lambda: desktop,
    )
    diagnostics = []

    elements = provider.perceive_structure_only(
        _structure_only_observation(),
        diagnostic_callback=diagnostics.append,
    )

    assert elements == ()
    assert any(
        record.get("diagnostic_type") == "root_descendants_failed"
        and record.get("error_type") == "RuntimeError"
        for record in diagnostics
    )


def test_structure_only_perception_reports_no_items_as_completed_empty_root():
    diagnostics = []
    provider = WindowHubUIAutomationProvider(
        desktop_factory=lambda: _StructureOnlyDesktop(
            _StructureOnlyUIAWindow(())
        ),
    )

    elements = provider.perceive_structure_only(
        _structure_only_observation(),
        diagnostic_callback=diagnostics.append,
    )

    assert elements == ()
    assert any(
        record.get("diagnostic_type") == "root_scan_completed"
        and record.get("descendant_count") == 0
        for record in diagnostics
    )


def test_structure_only_perception_never_scans_unowned_foreground_window():
    unrelated_grid = _StructureOnlyUIAItem(
        control_type="DataGrid",
        automation_id="PART_GridControl",
        runtime_id=(9, 8, 21),
    )
    main_window = _StructureOnlyUIAWindow(())
    unrelated_window = _StructureOnlyUIAWindow((unrelated_grid,))
    desktop = _StructureOnlyDesktop(
        windows={
            991: main_window,
            992: unrelated_window,
        }
    )
    provider = WindowHubUIAutomationProvider(
        desktop_factory=lambda: desktop,
    )
    observation = _structure_only_observation()
    observation = EnvironmentObservation(
        state=observation.state,
        metadata={
            **observation.metadata,
            "foreground_window_handle": 992,
            "foreground_root_owner_handle": 777,
        },
    )

    elements = provider.perceive_structure_only(observation)

    assert elements == ()
    assert desktop.requested_handles == [991]


def test_structure_only_popup_target_is_rejected_after_owner_relationship_changes():
    lookup = _StructureOnlyUIAItem(
        control_type="Custom",
        automation_id="IDC_ZAMAWIAJACY",
        class_name="lookupedit",
        runtime_id=(9, 8, 31),
    )
    grid = _StructureOnlyUIAItem(
        control_type="DataGrid",
        automation_id="PART_GridControl",
        runtime_id=(9, 8, 32),
        parent=lookup,
    )
    popup_window = _StructureOnlyUIAWindow((lookup, grid))
    desktop = _StructureOnlyDesktop(
        windows={
            991: _StructureOnlyUIAWindow(()),
            992: popup_window,
        }
    )
    provider = WindowHubUIAutomationProvider(
        desktop_factory=lambda: desktop,
    )
    observation = _structure_only_observation()
    owned_observation = EnvironmentObservation(
        state=observation.state,
        metadata={
            **observation.metadata,
            "foreground_window_handle": 992,
            "foreground_root_owner_handle": 991,
        },
    )
    table = provider.perceive_structure_only(owned_observation)[0]

    changed_observation = EnvironmentObservation(
        state=observation.state,
        metadata={
            **observation.metadata,
            "foreground_window_handle": 992,
            "foreground_root_owner_handle": 777,
        },
    )
    adapter = WindowHubLookupGridAdapter(provider=provider)

    try:
        adapter.resolve_current_grid(table, changed_observation)
    except RuntimeError as exc:
        assert "popup_owner_changed" in str(exc)
    else:
        raise AssertionError("A popup with a changed owner was accepted")
