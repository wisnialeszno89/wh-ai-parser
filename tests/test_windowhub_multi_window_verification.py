from __future__ import annotations

from types import SimpleNamespace

from app.agent.agent_action import AgentAction
from app.agent.agent_intent import AgentIntent
from app.agent.environment.environment_observation import EnvironmentObservation
from app.agent.environment.environment_state import EnvironmentState
from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.screen_scene import ScreenScene
from app.agent.planning.action_plan import ActionPlan
from app.agent.planning.action_step import ActionStep
from app.agent.runtime.resumable_task import TaskCheckpoint, TaskStatus
from app.agent.runtime.windowhub_resumable_task_host import (
    WindowHubResumableTaskHost,
    verify_windowhub_final_state,
)


REVIEWED_ROWS = (
    (1, 1120, 1440, 4),
    (2, 1100, 1440, 2),
    (3, 700, 1440, 2),
    (4, 2200, 1440, 1),
    (5, 1050, 2170, 1),
    (6, 2200, 1440, 1),
)


def checkpoint() -> TaskCheckpoint:
    windows = [
        {
            "position_number": position,
            "width_mm": width,
            "height_mm": height,
            "quantity": quantity,
            "human_confirmed": True,
        }
        for position, width, height, quantity in REVIEWED_ROWS
    ]
    return TaskCheckpoint(
        task_id="multi-window-check",
        goal="Prepare exactly the human-reviewed window rows as a draft.",
        facts={
            "product_type": "window",
            "windows": windows,
            "position_count": len(windows),
            "total_quantity": sum(row[3] for row in REVIEWED_ROWS),
            "human_review_confirmed": True,
        },
        required_fields=("product_type", "windows", "position_count", "total_quantity"),
        status=TaskStatus.READY,
        max_actions=8,
        max_reasoning_calls=8,
    )


def grid_cell(
    row: int,
    column: int,
    value: str,
    *,
    label: str | None = None,
    row_count: int = 6,
    column_count: int = 3,
    scope: str = "New draft",
    grid_id: str = "new-draft-lines",
    value_available: bool = True,
) -> ScreenElement:
    return ScreenElement(
        kind="gridcell",
        label=label or value,
        confidence=0.99,
        metadata={
            "source": "windowhub_ui_automation",
            "uia_grid_cell_observation": True,
            "uia_grid_id": grid_id,
            "uia_grid_row_index": row,
            "uia_grid_column_index": column,
            "uia_grid_row_count": row_count,
            "uia_grid_column_count": column_count,
            "uia_grid_enumeration_truncated": False,
            "document_scope": scope,
            "current_value": value if value_available else None,
            "current_value_available": value_available,
            "current_value_source": "uia_legacy_accessible" if value_available else None,
        },
    )


def make_scene(*elements, active_document="New draft") -> ScreenScene:
    return ScreenScene(
        observation=EnvironmentObservation(
            state=EnvironmentState(
                active_application="WindowHub",
                active_window_title="Okna - WindowHub",
            ),
        ),
        elements=tuple(elements),
        metadata={"active_document": active_document},
    )


def combined_dimension_grid(*, scope="New draft", wrong_row=None, incomplete=False):
    elements = []
    for row_index, (_position, width, height, quantity) in enumerate(REVIEWED_ROWS):
        dimension_value = f"{width} x {height}"
        if wrong_row == row_index:
            dimension_value = f"{width} x {height - 1}"
        elements.extend((
            grid_cell(row_index, 0, "Okno", label="Okno", scope=scope),
            grid_cell(row_index, 1, dimension_value, scope=scope),
            grid_cell(
                row_index,
                2,
                str(quantity),
                label="Menge",
                scope=scope,
                value_available=not (incomplete and row_index == 2),
            ),
        ))
    return elements


def split_dimension_grid(*, scope="New draft"):
    elements = []
    for row_index, (_position, width, height, quantity) in enumerate(REVIEWED_ROWS):
        elements.extend((
            grid_cell(row_index, 0, "Okno", label="Okno", column_count=4, scope=scope),
            grid_cell(row_index, 1, str(width), column_count=4, scope=scope),
            grid_cell(row_index, 2, str(height), column_count=4, scope=scope),
            grid_cell(row_index, 3, str(quantity), label="Menge", column_count=4, scope=scope),
        ))
    for element in elements:
        element.metadata["uia_grid_column_count"] = 4
    return elements


def test_final_verifier_matches_every_combined_dimension_row_in_active_document():
    scene = make_scene(*combined_dimension_grid())

    result = verify_windowhub_final_state(checkpoint(), scene)

    assert result.verified is True
    assert result.missing_fields == ()
    row_evidence = [
        item for item in result.evidence
        if isinstance(item.get("field"), str) and item["field"].startswith("windows[")
    ]
    assert len(row_evidence) == 6
    assert {item["position_number"] for item in row_evidence} == {1, 2, 3, 4, 5, 6}
    assert sum(item["observed_quantity"] for item in row_evidence) == 11
    assert all(item["verification"] == "complete_active_document_grid_row" for item in row_evidence)


def test_final_verifier_supports_separate_width_height_and_quantity_columns():
    scene = make_scene(*split_dimension_grid())

    result = verify_windowhub_final_state(checkpoint(), scene)

    assert result.verified is True
    assert all(
        item.get("grid_layout") == "separate_dimensions"
        for item in result.evidence
        if str(item.get("field", "")).startswith("windows[")
    )


def test_final_verifier_rejects_wrong_dimension_even_when_all_rows_are_readable():
    scene = make_scene(*combined_dimension_grid(wrong_row=3))

    result = verify_windowhub_final_state(checkpoint(), scene)

    assert result.verified is False
    assert "windows" in result.missing_fields
    assert "uniquely matches" in result.reason


def test_final_verifier_rejects_grid_that_is_not_scoped_to_active_document():
    scene = make_scene(*combined_dimension_grid(scope="Existing offer OFR/123"))

    result = verify_windowhub_final_state(checkpoint(), scene)

    assert result.verified is False
    assert "active-document grid" in result.reason


def test_final_verifier_rejects_unreadable_or_incomplete_grid():
    scene = make_scene(*combined_dimension_grid(incomplete=True))

    result = verify_windowhub_final_state(checkpoint(), scene)

    assert result.verified is False
    assert "uniquely matches" in result.reason


def test_final_verifier_rejects_extra_or_missing_grid_rows():
    elements = combined_dimension_grid()
    elements = [e for e in elements if e.metadata["uia_grid_row_index"] != 4]
    scene = make_scene(*elements)

    result = verify_windowhub_final_state(checkpoint(), scene)

    assert result.verified is False
    assert "uniquely matches" in result.reason


class PlannerWithOneWrite:
    def __init__(self, *, target: str, value: str):
        self.target = target
        self.value = value

    def prepare(self, request, initial_scene=None, **kwargs):
        action = AgentAction(
            name="write_text",
            description="Enter value into the current position.",
            target=self.target,
            value=self.value,
        )
        plan = ActionPlan(
            intent=AgentIntent.CREATE_QUOTE,
            steps=(ActionStep(index=1, action=action),),
            confidence=1.0,
        )
        return SimpleNamespace(
            plan=plan,
            requires_manual_review=False,
            intent=AgentIntent.CREATE_QUOTE,
        )


class NoopControlLoop:
    def observe_scene(self):
        raise AssertionError("Test must not observe the actual desktop.")

    def run(self, **kwargs):
        raise AssertionError("Test must not execute a GUI action.")


def planner_scene(*, include_second_position=False):
    elements = [
        ScreenElement(
            kind="text",
            label="Position 1",
            metadata={"document_scope": "New draft"},
        ),
        ScreenElement(
            kind="edit",
            label="Szerokość",
            interaction_capability="writable",
            metadata={
                "current_value": "",
                "document_scope": "New draft",
            },
        ),
    ]
    if include_second_position:
        elements.append(ScreenElement(
            kind="text",
            label="Position 2",
            metadata={"document_scope": "New draft"},
        ))
    return make_scene(*elements)


def test_planner_guard_rejects_width_that_conflicts_with_current_reviewed_position():
    host = WindowHubResumableTaskHost(
        control_loop=NoopControlLoop(),
        orchestrator=PlannerWithOneWrite(target="Szerokość", value="1100"),
    )

    decision = host._plan_next(checkpoint(), planner_scene())

    assert decision.action is None
    assert any("conflicts with its human-reviewed value" in item for item in decision.unresolved_issues)


def test_planner_guard_allows_exact_value_for_explicit_current_position():
    host = WindowHubResumableTaskHost(
        control_loop=NoopControlLoop(),
        orchestrator=PlannerWithOneWrite(target="Szerokość", value="1120"),
    )

    decision = host._plan_next(checkpoint(), planner_scene())

    assert decision.action is not None
    assert decision.action.value == "1120"


def test_planner_guard_stops_when_current_position_is_ambiguous():
    host = WindowHubResumableTaskHost(
        control_loop=NoopControlLoop(),
        orchestrator=PlannerWithOneWrite(target="Szerokość", value="1120"),
    )

    decision = host._plan_next(
        checkpoint(),
        planner_scene(include_second_position=True),
    )

    assert decision.action is None
    assert any("unambiguous visible position" in item for item in decision.unresolved_issues)
