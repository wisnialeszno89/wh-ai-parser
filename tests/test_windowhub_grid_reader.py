from app.agent.environment.environment_observation import (
    EnvironmentObservation,
)
from app.agent.environment.environment_state import EnvironmentState
from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.screen_scene import ScreenScene
from app.agent.perception.windowhub_grid_reader import WindowHubGridReader


def make_scene(*elements, active_document="OFR/4024"):
    return ScreenScene(
        observation=EnvironmentObservation(
            state=EnvironmentState(
                active_window_title="Okna - WindowHub",
            ),
        ),
        elements=tuple(elements),
        metadata={"active_document": active_document},
    )


def grid_cell(
    *,
    row,
    column,
    value,
    label=None,
    grid_id="grid-a",
    scope="OFR/4024",
    rows=2,
    columns=2,
    value_available=True,
    truncated=False,
):
    metadata = {
        "source": "windowhub_ui_automation",
        "uia_grid_cell_observation": True,
        "uia_grid_id": grid_id,
        "uia_grid_row_index": row,
        "uia_grid_column_index": column,
        "uia_grid_row_count": rows,
        "uia_grid_column_count": columns,
        "uia_grid_enumeration_truncated": truncated,
        "document_scope": scope,
        "current_value": value if value_available else None,
        "current_value_available": value_available,
        "current_value_source": "uia_legacy_accessible" if value_available else None,
    }
    return ScreenElement(
        kind="gridcell",
        label=label or f"Cell {row},{column}",
        confidence=0.99,
        metadata=metadata,
    )


def test_reader_groups_cells_by_row_and_column_and_preserves_blank_values():
    scene = make_scene(
        grid_cell(row=0, column=0, value="A"),
        grid_cell(row=0, column=1, value=""),
        grid_cell(row=1, column=0, value="B", rows=2, columns=2),
    )

    grids = WindowHubGridReader().read_active_document(scene)

    assert len(grids) == 1
    grid = grids[0]
    assert grid.document_scope == "OFR/4024"
    assert grid.scope_status == "active_document"
    assert grid.row_count == 2
    assert grid.column_count == 2
    assert grid.rows[0][0].value == "A"
    assert grid.rows[0][1].value == ""
    assert grid.rows[0][1].value_available is True
    assert grid.rows[1][0].value == "B"
    assert grid.rows[1][1] is None
    assert grid.missing_cell_count == 1
    assert grid.complete is False


def test_reader_keeps_values_that_were_not_readable_distinct_from_blank_values():
    scene = make_scene(
        grid_cell(row=0, column=0, value="", value_available=True),
        grid_cell(row=0, column=1, value=None, value_available=False),
    )

    grid = WindowHubGridReader().read_active_document(scene)[0]

    assert grid.rows[0][0].value == ""
    assert grid.rows[0][0].value_available is True
    assert grid.rows[0][1].value is None
    assert grid.rows[0][1].value_available is False
    assert grid.unreadable_value_count == 1


def test_reader_filters_other_documents_for_active_document_reads():
    scene = make_scene(
        grid_cell(row=0, column=0, value="active", grid_id="active-grid"),
        grid_cell(
            row=0,
            column=0,
            value="inactive",
            grid_id="other-grid",
            scope="OFR/4025",
            rows=1,
            columns=1,
        ),
    )

    reader = WindowHubGridReader()
    all_grids = reader.read(scene)
    active_grids = reader.read_active_document(scene)

    assert len(all_grids) == 2
    assert len(active_grids) == 1
    assert active_grids[0].grid_id == "active-grid"
    assert active_grids[0].rows[0][0].value == "active"
    assert next(
        grid for grid in all_grids if grid.grid_id == "other-grid"
    ).scope_status == "other_document"


def test_reader_fails_closed_when_active_document_is_unresolved():
    scene = make_scene(
        grid_cell(row=0, column=0, value="A"),
        active_document=None,
    )
    assert WindowHubGridReader().read_active_document(scene) == ()
    assert WindowHubGridReader().read(scene)[0].scope_status == "unresolved"


def test_reader_ignores_non_grid_elements_and_invalid_cell_coordinates():
    ordinary = ScreenElement(
        kind="text",
        label="Not a grid cell",
        metadata={"current_value": "ignored"},
    )
    invalid = grid_cell(row=-1, column=0, value="bad")
    missing_id = grid_cell(row=0, column=0, value="bad", grid_id="")

    grids = WindowHubGridReader().read(make_scene(ordinary, invalid, missing_id))

    assert grids == ()


def test_reader_marks_duplicate_coordinates_as_ambiguous():
    scene = make_scene(
        grid_cell(row=0, column=0, value="first", rows=1, columns=1),
        grid_cell(row=0, column=0, value="second", rows=1, columns=1),
    )

    grid = WindowHubGridReader().read_active_document(scene)[0]

    assert grid.duplicate_positions == ((0, 0),)
    assert grid.rows == ((None,),)
    assert grid.complete is False


def test_reader_avoids_allocating_an_unbounded_matrix_for_large_grids():
    scene = make_scene(
        grid_cell(
            row=0,
            column=0,
            value="A",
            rows=1000,
            columns=100,
            truncated=True,
        ),
    )

    grid = WindowHubGridReader().read_active_document(scene)[0]

    assert grid.matrix_omitted is True
    assert grid.rows == ()
    assert grid.truncated is True
    assert grid.complete is False
    assert grid.observed_cell_count == 1
