from types import SimpleNamespace

from app.agent.perception.screen_element import ScreenElement
from app.agent.runtime.read_only_observation_broker import (
    ObservationReadContext,
    ObservationRejected,
)
from app.agent.runtime.windowhub_uia_grid_table_reader import (
    WindowHubUIAGridTableReader,
    windowhub_grid_capability_spec,
)


class FakeCell:
    def __init__(self, value):
        self.element_info = SimpleNamespace(
            name=value,
            rich_text=None,
        )

    def window_text(self):
        return self.element_info.name or ""


class FakeGridPattern:
    def __init__(self, rows):
        self.rows = rows
        self.CurrentRowCount = len(rows)
        self.CurrentColumnCount = len(rows[0]) if rows else 2

    def GetItem(self, row, column):
        return FakeCell(self.rows[row][column])


class FakeTablePattern:
    def GetCurrentColumnHeaders(self):
        return [FakeCell("Firma"), FakeCell("Miasto")]


class FakeGrid:
    def __init__(self, rows):
        self.iface_grid = FakeGridPattern(rows)
        self.iface_table = FakeTablePattern()
        self.element_info = SimpleNamespace(
            control_type="DataGrid",
            runtime_id=(7, 10, 20),
        )


def make_target():
    return ScreenElement(
        kind="table",
        label="Tabela syntetyczna",
        metadata={
            "source": "windowhub_ui_automation",
            "uia_control_type": "datagrid",
            "uia_runtime_id": "7-10-20",
        },
    )


def make_context(
    *,
    max_items=5,
    max_result_bytes=8_192,
    deadline=100.0,
):
    return ObservationReadContext(
        task_id="synthetic-task",
        world_revision=1,
        max_items=max_items,
        max_result_bytes=max_result_bytes,
        deadline_monotonic=deadline,
    )


def make_rows():
    return [
        ["Firma A", "Miasto A"],
        ["Firma B", "Miasto B"],
        ["Firma C", "Miasto C"],
        ["Firma D", "Miasto D"],
    ]


def test_reader_returns_only_requested_bounded_grid_page():
    target = make_target()
    grid = FakeGrid(make_rows())
    reader = WindowHubUIAGridTableReader(
        grid_resolver=lambda resolved_target: grid,
        clock=lambda: 1.0,
    )

    result = reader(
        target,
        {"offset": 1, "limit": 2},
        make_context(max_items=2),
    )

    assert result.content == {
        "headers": ["Firma", "Miasto"],
        "rows": [
            ["Firma B", "Miasto B"],
            ["Firma C", "Miasto C"],
        ],
        "offset": 1,
        "has_more": True,
        "reported_row_count": 4,
    }
    assert any("not independently verified" in item for item in result.limitations)


def test_reader_uses_explicit_positional_headers_when_uia_has_no_headers():
    class GridWithoutHeaders(FakeGrid):
        def __init__(self, rows):
            super().__init__(rows)
            self.iface_table = None

    grid = GridWithoutHeaders(make_rows())
    reader = WindowHubUIAGridTableReader(
        grid_resolver=lambda target: grid,
        clock=lambda: 1.0,
    )

    result = reader(
        make_target(),
        {"offset": 0, "limit": 1},
        make_context(),
    )

    assert result.content["headers"] == ["Column 1", "Column 2"]
    assert any("positional labels" in item for item in result.limitations)


def test_reader_rejects_non_table_or_missing_runtime_identity():
    reader = WindowHubUIAGridTableReader(
        grid_resolver=lambda target: FakeGrid(make_rows()),
        clock=lambda: 1.0,
    )
    invalid = ScreenElement(
        kind="button",
        label="Open",
        metadata={"uia_control_type": "button"},
    )

    try:
        reader(
            invalid,
            {"offset": 0, "limit": 1},
            make_context(),
        )
    except ObservationRejected as exc:
        assert "uia_grid_target_invalid" in str(exc)
    else:
        raise AssertionError("Non-table target was accepted.")


def test_reader_rejects_resolver_returning_another_uia_element():
    class WrongGrid(FakeGrid):
        def __init__(self):
            super().__init__(make_rows())
            self.element_info = SimpleNamespace(
                control_type="DataGrid",
                runtime_id=(7, 999, 999),
            )

    reader = WindowHubUIAGridTableReader(
        grid_resolver=lambda target: WrongGrid(),
        clock=lambda: 1.0,
    )

    try:
        reader(
            make_target(),
            {"offset": 0, "limit": 1},
            make_context(),
        )
    except ObservationRejected as exc:
        assert "uia_grid_resolved_identity_mismatch" in str(exc)
    else:
        raise AssertionError("Mismatched UIA target was accepted.")


def test_reader_rejects_pages_larger_than_task_item_budget():
    reader = WindowHubUIAGridTableReader(
        grid_resolver=lambda target: FakeGrid(make_rows()),
        clock=lambda: 1.0,
    )

    try:
        reader(
            make_target(),
            {"offset": 0, "limit": 6},
            make_context(max_items=5),
        )
    except ObservationRejected as exc:
        assert "uia_grid_page_parameters_invalid" in str(exc)
    else:
        raise AssertionError("Oversized page was accepted.")


def test_reader_rejects_text_query_instead_of_scanning_unbounded_rows():
    reader = WindowHubUIAGridTableReader(
        grid_resolver=lambda target: FakeGrid(make_rows()),
        clock=lambda: 1.0,
    )

    try:
        reader(
            make_target(),
            {"offset": 0, "limit": 1, "text_query": "Firma"},
            make_context(),
        )
    except ObservationRejected as exc:
        assert "uia_grid_text_query_unsupported" in str(exc)
    else:
        raise AssertionError("Unbounded client-side filtering was accepted.")


def test_reader_rejects_result_exceeding_byte_budget():
    rows = [["X" * 800, "Y" * 800]]
    reader = WindowHubUIAGridTableReader(
        grid_resolver=lambda target: FakeGrid(rows),
        clock=lambda: 1.0,
    )

    try:
        reader(
            make_target(),
            {"offset": 0, "limit": 1},
            make_context(max_result_bytes=1_024),
        )
    except ObservationRejected as exc:
        assert "byte_budget_exceeded" in str(exc)
    else:
        raise AssertionError("Oversized page was accepted.")


def test_reader_observes_deadline_between_grid_cells():
    now = [0.0]

    class SlowGridPattern(FakeGridPattern):
        def GetItem(self, row, column):
            now[0] += 1.0
            return super().GetItem(row, column)

    class SlowGrid(FakeGrid):
        def __init__(self, rows):
            super().__init__(rows)
            self.iface_grid = SlowGridPattern(rows)

    reader = WindowHubUIAGridTableReader(
        grid_resolver=lambda target: SlowGrid(make_rows()),
        clock=lambda: now[0],
    )

    try:
        reader(
            make_target(),
            {"offset": 0, "limit": 1},
            make_context(deadline=0.5),
        )
    except ObservationRejected as exc:
        assert "time_budget_exceeded" in str(exc)
    else:
        raise AssertionError("Late UIA cell read was accepted.")


def test_windowhub_grid_capability_is_fail_closed_for_business_records():
    spec = windowhub_grid_capability_spec()
    assert spec.input_contract == "table_page_v1"
    assert spec.data_classification == "business_records"
    assert spec.read_only is True
    assert spec.max_items == 10
    assert "business_records" == spec.data_classification
