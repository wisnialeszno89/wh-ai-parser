from types import SimpleNamespace

from app.agent.environment.environment_observation import EnvironmentObservation
from app.agent.environment.environment_state import EnvironmentState
from app.agent.perception.windowhub_ui_automation_provider import (
    WindowHubUIAutomationProvider,
)
from app.agent.runtime.read_only_observation_broker import (
    ObservationReadContext,
)
from app.agent.runtime.windowhub_lookup_grid_adapter import (
    WINDOWHUB_CLIENT_LOOKUP_AUTOMATION_ID,
    WINDOWHUB_LOOKUP_GRID_AUTOMATION_ID,
    WindowHubLookupGridAdapter,
)
from app.agent.runtime.windowhub_uia_grid_structure_reader import (
    WindowHubUIAGridStructureReader,
)


class FakeUIAItem:
    def __init__(
        self,
        *,
        name="",
        control_type="Custom",
        class_name="",
        automation_id="",
        runtime_id=(1, 2, 3),
        enabled=True,
        visible=True,
        parent=None,
    ):
        self.element_info = SimpleNamespace(
            name=name,
            control_type=control_type,
            class_name=class_name,
            automation_id=automation_id,
            runtime_id=runtime_id,
            enabled=enabled,
            visible=visible,
            rich_text=None,
        )
        self._parent = parent
        self._rectangle = SimpleNamespace(
            left=100,
            top=200,
            width=lambda: 420,
            height=lambda: 260,
        )

    def parent(self):
        return self._parent

    def rectangle(self):
        return self._rectangle


class FakeUIAWindow:
    def __init__(self, items):
        self._items = tuple(items)

    def window_text(self):
        return "Okna - WindowHub"

    def descendants(self):
        return self._items


class FakeDesktop:
    def __init__(self, window):
        self._window = window

    def get_active(self):
        return self._window


class FakeGridPattern:
    CurrentRowCount = 17
    CurrentColumnCount = 4

    def __init__(self):
        self.cell_reads = 0

    def GetItem(self, _row, _column):
        self.cell_reads += 1
        raise AssertionError("Lookup/Grid structure adapter must not read cells")


def make_observation():
    return EnvironmentObservation(
        state=EnvironmentState(
            active_application="WindowHub",
            active_window_title="Okna - WindowHub",
        ),
        metadata={
            "window_rect": SimpleNamespace(
                left=0,
                top=0,
                width=1440,
                height=900,
            )
        },
    )


def make_window(
    *,
    client_lookup_parent=True,
    wrong_lookup_ancestor_class=False,
):
    lookup = FakeUIAItem(
        name="Zamawiający",
        control_type="Button",
        class_name="lookupedit",
        automation_id=WINDOWHUB_CLIENT_LOOKUP_AUTOMATION_ID,
        runtime_id=(4, 10, 20),
    )
    container = FakeUIAItem(
        name="",
        control_type="Custom",
        class_name="popupcontent",
        runtime_id=(4, 10, 21),
        parent=(
            lookup
            if client_lookup_parent
            else FakeUIAItem(
                name="",
                control_type="Button" if wrong_lookup_ancestor_class else "Pane",
                class_name=(
                    "otherlookup"
                    if wrong_lookup_ancestor_class
                    else "documentview"
                ),
                automation_id=(
                    WINDOWHUB_CLIENT_LOOKUP_AUTOMATION_ID
                    if wrong_lookup_ancestor_class
                    else "IDC_DOKUMENT"
                ),
                runtime_id=(4, 10, 22),
            )
        ),
    )
    grid = FakeUIAItem(
        name="",
        control_type="DataGrid",
        class_name="",
        automation_id=WINDOWHUB_LOOKUP_GRID_AUTOMATION_ID,
        runtime_id=(7, 18708, 63003992),
        parent=container,
    )
    grid.iface_grid = FakeGridPattern()
    grid.iface_table = object()
    return FakeUIAWindow((lookup, container, grid)), grid


def make_adapter(window):
    desktop = FakeDesktop(window)
    provider = WindowHubUIAutomationProvider(
        desktop_factory=lambda: desktop,
    )
    return WindowHubLookupGridAdapter(provider=provider), provider


def make_client_grid_target():
    window, _grid = make_window()
    adapter, provider = make_adapter(window)
    observation = make_observation()
    elements = provider.perceive(observation)
    scene = SimpleNamespace(
        observation=observation,
        elements=elements,
        metadata={},
        active_document=None,
    )
    result = adapter.resolve_scene_target(scene)
    assert result.resolved is True
    return result.element, adapter, provider, observation


def test_adapter_resolves_only_grid_inside_client_lookupedit():
    window, _grid = make_window(client_lookup_parent=True)
    adapter, provider = make_adapter(window)
    observation = make_observation()

    elements = provider.perceive(observation)
    scene = SimpleNamespace(
        observation=observation,
        elements=elements,
        metadata={},
        active_document=None,
    )

    result = adapter.resolve_scene_target(scene)

    assert result.resolved is True
    assert result.element is not None
    assert result.element.kind == "table"
    assert result.element.metadata["automation_id"] == "PART_GridControl"
    ancestors = result.element.metadata["uia_ancestor_structure"]
    assert any(
        item["automation_id"] == "idc_zamawiajacy"
        and item["class_name"] == "lookupedit"
        for item in ancestors
    )


def test_adapter_rejects_other_datagrid_not_contained_by_client_lookup():
    window, _grid = make_window(client_lookup_parent=False)
    adapter, provider = make_adapter(window)
    observation = make_observation()
    elements = provider.perceive(observation)
    scene = SimpleNamespace(
        observation=observation,
        elements=elements,
        metadata={},
        active_document=None,
    )

    result = adapter.resolve_scene_target(scene)

    assert result.resolved is False
    assert result.element is None


def test_adapter_re_resolves_current_grid_and_verifies_lookup_ancestry():
    target, _old_adapter, _old_provider, observation = make_client_grid_target()
    current_window, current_grid = make_window(client_lookup_parent=True)
    adapter, _provider = make_adapter(current_window)

    resolved = adapter.resolve_current_grid(target, observation)

    assert resolved is current_grid


def test_adapter_rejects_grid_if_live_lookup_ancestry_has_changed():
    target, _old_adapter, _old_provider, observation = make_client_grid_target()
    changed_window, _changed_grid = make_window(client_lookup_parent=False)
    adapter, _provider = make_adapter(changed_window)

    try:
        adapter.resolve_current_grid(target, observation)
    except LookupError as exc:
        assert "not_unique_or_not_found" in str(exc)
    else:
        raise AssertionError("A grid outside the Client LookupEdit was accepted")


def test_adapter_connects_to_structure_reader_without_reading_cells():
    target, adapter, _provider, observation = make_client_grid_target()
    current_window, current_grid = make_window(client_lookup_parent=True)
    current_adapter, _current_provider = make_adapter(current_window)
    pattern = current_grid.iface_grid

    reader = WindowHubUIAGridStructureReader(
        grid_resolver=current_adapter.resolver_for_observation(observation),
        clock=lambda: 1.0,
    )
    context = ObservationReadContext(
        task_id="lookup-grid-task",
        world_revision=1,
        max_items=10,
        max_result_bytes=2_048,
        deadline_monotonic=100.0,
    )

    result = reader(
        target,
        {"fields": ("row_count", "column_count", "grid_pattern_available")},
        context,
    )

    assert result.content == {
        "fields": {
            "row_count": 17,
            "column_count": 4,
            "grid_pattern_available": True,
        }
    }
    assert pattern.cell_reads == 0



def test_adapter_rejects_same_lookup_automation_id_on_wrong_ancestor_class():
    wrong_window, _wrong_grid = make_window(
        client_lookup_parent=False,
        wrong_lookup_ancestor_class=True,
    )
    adapter, _provider = make_adapter(wrong_window)
    target, _old_adapter, _old_provider, observation = make_client_grid_target()

    try:
        adapter.resolve_current_grid(target, observation)
    except LookupError as exc:
        assert "not_unique_or_not_found" in str(exc)
    else:
        raise AssertionError(
            "A grid under a different class with the same AutomationId was accepted"
        )
