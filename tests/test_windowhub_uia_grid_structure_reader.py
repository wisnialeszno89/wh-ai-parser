from types import SimpleNamespace

from app.agent.bridge.agent_task_v2_world_builder import (
    AgentTaskV2WorldBuilder,
)
from app.agent.environment.environment_observation import EnvironmentObservation
from app.agent.environment.environment_state import EnvironmentState
from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.screen_scene import ScreenScene
from app.agent.runtime.read_only_observation_broker import (
    ObservationReadContext,
    ObservationRejected,
    ReadOnlyObservationBroker,
)
from app.agent.runtime.windowhub_uia_grid_structure_reader import (
    WindowHubUIAGridStructureReader,
    windowhub_grid_structure_capability_spec,
)


class FakeGridPattern:
    CurrentRowCount = 6818
    CurrentColumnCount = 4

    def __init__(self):
        self.cell_reads = 0

    def GetItem(self, row, column):
        self.cell_reads += 1
        raise AssertionError("Structure reader must never read cells.")


class FakeGrid:
    def __init__(self, *, runtime_id=(7, 18708, 63003992), table_pattern=True):
        self.iface_grid = FakeGridPattern()
        self.iface_table = object() if table_pattern else None
        self.element_info = SimpleNamespace(
            control_type="DataGrid",
            runtime_id=runtime_id,
        )


def make_target():
    return ScreenElement(
        kind="table",
        label="Tabela danych",
        metadata={
            "source": "windowhub_ui_automation",
            "uia_control_type": "datagrid",
            "uia_runtime_id": "7-18708-63003992",
        },
    )


def make_context(*, deadline=100.0, max_result_bytes=2_048):
    return ObservationReadContext(
        task_id="structure-task",
        world_revision=3,
        max_items=10,
        max_result_bytes=max_result_bytes,
        deadline_monotonic=deadline,
    )


def test_structure_reader_returns_only_requested_ui_structure_fields():
    target = make_target()
    grid = FakeGrid()
    reader = WindowHubUIAGridStructureReader(
        grid_resolver=lambda resolved: grid,
        clock=lambda: 1.0,
    )

    result = reader(
        target,
        {
            "fields": (
                "row_count",
                "column_count",
                "grid_pattern_available",
                "table_pattern_available",
            )
        },
        make_context(),
    )

    assert result.content == {
        "fields": {
            "row_count": 6818,
            "column_count": 4,
            "grid_pattern_available": True,
            "table_pattern_available": True,
        }
    }
    assert grid.iface_grid.cell_reads == 0
    assert any("not verified record counts" in item for item in result.limitations)
    assert any("No table cells" in item for item in result.limitations)


def test_structure_reader_reads_only_fields_requested_by_caller():
    grid = FakeGrid()
    reader = WindowHubUIAGridStructureReader(
        grid_resolver=lambda target: grid,
        clock=lambda: 1.0,
    )

    result = reader(
        make_target(),
        {"fields": ("column_count",)},
        make_context(),
    )

    assert result.content == {"fields": {"column_count": 4}}
    assert grid.iface_grid.cell_reads == 0


def test_structure_reader_rejects_business_data_fields_and_arbitrary_names():
    reader = WindowHubUIAGridStructureReader(
        grid_resolver=lambda target: FakeGrid(),
        clock=lambda: 1.0,
    )

    for fields in (
        ("customer_name",),
        ("row_count", "first_row"),
        ("selector",),
    ):
        try:
            reader(
                make_target(),
                {"fields": fields},
                make_context(),
            )
        except ObservationRejected as exc:
            assert "field_not_allowed" in str(exc)
        else:
            raise AssertionError(f"Unexpected fields accepted: {fields}")


def test_structure_reader_rejects_stale_or_wrong_grid_identity():
    grid = FakeGrid(runtime_id=(7, 999, 999))
    reader = WindowHubUIAGridStructureReader(
        grid_resolver=lambda target: grid,
        clock=lambda: 1.0,
    )

    try:
        reader(
            make_target(),
            {"fields": ("row_count",)},
            make_context(),
        )
    except ObservationRejected as exc:
        assert "identity_mismatch" in str(exc)
    else:
        raise AssertionError("Mismatched UIA identity was accepted.")


def test_structure_reader_reports_table_pattern_absence_without_reading_cells():
    grid = FakeGrid(table_pattern=False)
    reader = WindowHubUIAGridStructureReader(
        grid_resolver=lambda target: grid,
        clock=lambda: 1.0,
    )

    result = reader(
        make_target(),
        {"fields": ("table_pattern_available",)},
        make_context(),
    )

    assert result.content == {
        "fields": {"table_pattern_available": False}
    }
    assert grid.iface_grid.cell_reads == 0


def test_structure_reader_enforces_deadline():
    now = [0.0]

    def clock():
        return now[0]

    def resolve(target):
        now[0] = 2.0
        return FakeGrid()

    reader = WindowHubUIAGridStructureReader(
        grid_resolver=resolve,
        clock=clock,
    )

    try:
        reader(
            make_target(),
            {"fields": ("row_count",)},
            make_context(deadline=1.0),
        )
    except ObservationRejected as exc:
        assert "time_budget_exceeded" in str(exc)
    else:
        raise AssertionError("Expired observation was accepted.")


def test_structure_reader_capability_uses_default_authorized_classification():
    spec = windowhub_grid_structure_capability_spec()
    assert spec.input_contract == "entity_inspection_v1"
    assert spec.data_classification == "ui_structure"
    assert spec.read_only is True


def test_default_broker_allows_structure_metadata_but_never_reads_cells():
    table = make_target()
    scene = ScreenScene(
        observation=EnvironmentObservation(
            state=EnvironmentState(
                active_application="WindowHub",
                active_window_title="Nowa oferta",
            )
        ),
        elements=(table,),
    )
    snapshot = AgentTaskV2WorldBuilder().build(
        scene,
        task_id="structure-task",
        world_revision=3,
        observed_at="2026-11-02T07:00:00Z",
    )
    grid = FakeGrid()
    reader = WindowHubUIAGridStructureReader(
        grid_resolver=lambda target: grid,
        clock=lambda: 1.0,
    )
    broker = ReadOnlyObservationBroker()
    broker.register(windowhub_grid_structure_capability_spec(), reader)
    descriptor = broker.bind(
        snapshot,
        capability_name="windowhub_inspect_grid_structure",
        target_ref="ent_0001",
    )

    evidence = broker.observe(
        {
            "capability_id": descriptor["id"],
            "target_ref": "ent_0001",
            "parameters": {
                "fields": ["row_count", "column_count"]
            },
            "based_on_world_revision": 3,
        },
        task_id="structure-task",
        world_revision=3,
        max_observation_items=10,
        max_evidence_bytes=2_048,
    )

    assert evidence["source"] == "uia_grid_structure"
    assert evidence["content"] == {
        "fields": {"row_count": 6818, "column_count": 4}
    }
    assert grid.iface_grid.cell_reads == 0
