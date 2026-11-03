from app.agent.environment.environment_observation import EnvironmentObservation
from app.agent.environment.environment_state import EnvironmentState
from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.screen_scene import ScreenScene
from app.agent.perception.semantic_target_query import (
    SemanticAncestorConstraint,
    SemanticTargetQuery,
)
from app.agent.perception.target_resolver import TargetResolver


def _scene(*elements):
    return ScreenScene(
        observation=EnvironmentObservation(
            state=EnvironmentState(
                active_application="WindowHub",
                active_window_title="Okna - WindowHub",
            )
        ),
        elements=tuple(elements),
    )


def _client_grid(label="Zamawiający", *, runtime_id="grid-1"):
    return ScreenElement(
        kind="table",
        label=label,
        metadata={
            "source": "windowhub_ui_automation",
            "automation_id": "PART_GridControl",
            "uia_control_type": "datagrid",
            "uia_runtime_id": runtime_id,
            "uia_ancestor_structure": (
                {
                    "control_type": "custom",
                    "class_name": "popupcontent",
                    "automation_id": "",
                },
                {
                    "control_type": "button",
                    "class_name": "lookupedit",
                    "automation_id": "IDC_ZAMAWIAJACY",
                },
            ),
        },
    )


def _query():
    return SemanticTargetQuery(
        role="table",
        automation_id="PART_GridControl",
        within=SemanticAncestorConstraint(
            control_type="button",
            class_name="lookupedit",
            automation_id="IDC_ZAMAWIAJACY",
        ),
        description="WindowHub Client Lookup grid",
    )


def test_semantic_resolver_matches_grid_by_role_and_lookup_ancestry():
    unrelated = ScreenElement(
        kind="table",
        label="Tabela danych",
        metadata={
            "source": "windowhub_ui_automation",
            "automation_id": "PART_GridControl",
            "uia_control_type": "datagrid",
            "uia_runtime_id": "other-grid",
            "uia_ancestor_structure": (
                {
                    "control_type": "pane",
                    "class_name": "documentview",
                    "automation_id": "IDC_DOKUMENT",
                },
            ),
        },
    )
    client_grid = _client_grid()

    result = TargetResolver().resolve(
        _scene(unrelated, client_grid),
        _query(),
    )

    assert result.resolved is True
    assert result.element is client_grid
    assert result.score == 0.99
    assert "ancestor" in result.reason


def test_semantic_resolver_rejects_grid_without_required_lookup_parent():
    unrelated = ScreenElement(
        kind="table",
        label="Zamawiający",
        metadata={
            "source": "windowhub_ui_automation",
            "automation_id": "PART_GridControl",
            "uia_control_type": "datagrid",
            "uia_runtime_id": "other-grid",
            "uia_ancestor_structure": (
                {
                    "control_type": "pane",
                    "class_name": "documentview",
                    "automation_id": "",
                },
            ),
        },
    )

    result = TargetResolver().resolve(
        _scene(unrelated),
        _query(),
    )

    assert result.resolved is False
    assert result.element is None
    assert "No screen element" in result.reason


def test_semantic_resolver_rejects_multiple_grids_under_same_lookup():
    first = _client_grid(runtime_id="grid-1")
    second = _client_grid(runtime_id="grid-2")

    result = TargetResolver().resolve(
        _scene(first, second),
        _query(),
    )

    assert result.resolved is False
    assert result.element is None
    assert "Multiple screen elements" in result.reason


def test_semantic_query_requires_at_least_one_selector():
    try:
        SemanticTargetQuery()
    except ValueError as exc:
        assert "has_no_selector" in str(exc)
    else:
        raise AssertionError("An empty semantic query must be rejected")


def test_ancestor_constraint_requires_at_least_one_property():
    try:
        SemanticAncestorConstraint()
    except ValueError as exc:
        assert "constraint_empty" in str(exc)
    else:
        raise AssertionError("An empty ancestor constraint must be rejected")


def _uia_edit(label, automation_id, runtime_id):
    return ScreenElement(
        kind="edit",
        label=label,
        metadata={
            "source": "windows_ui_automation",
            "automation_id": automation_id,
            "uia_control_type": "edit",
            "uia_runtime_id": runtime_id,
        },
    )


def test_semantic_target_resolves_duplicate_labels_by_local_uia_runtime_id():
    first = _uia_edit("Szerokość", "1000", "[window-width]")
    second = _uia_edit("Szerokość", "1014", "[sash-width]")
    query = SemanticTargetQuery(
        role="edit",
        label="Szerokość",
        automation_id="1014",
        uia_runtime_id="[sash-width]",
        description="Exact sash width edit",
    )

    result = TargetResolver().resolve(_scene(first, second), query)

    assert result.resolved is True
    assert result.element is second
    assert "uia_runtime_id" in result.reason or result.score == 0.99


def test_semantic_target_rejects_duplicate_uia_runtime_id():
    first = _uia_edit("Szerokość", "1000", "[duplicate]")
    second = _uia_edit("Wysokość", "1001", "[duplicate]")
    query = SemanticTargetQuery(
        role="edit",
        uia_runtime_id="[duplicate]",
        description="Duplicate runtime identity",
    )

    result = TargetResolver().resolve(_scene(first, second), query)

    assert result.resolved is False
    assert result.element is None


def test_semantic_target_runtime_id_is_scoped_to_windows_uia_sources():
    foreign = ScreenElement(
        kind="edit",
        label="Szerokość",
        metadata={
            "source": "browser_dom",
            "uia_control_type": "edit",
            "uia_runtime_id": "[target]",
        },
    )
    query = SemanticTargetQuery(
        role="edit",
        uia_runtime_id="[target]",
        description="Windows UIA-only target",
    )

    result = TargetResolver().resolve(_scene(foreign), query)

    assert result.resolved is False
    assert result.element is None


def test_semantic_target_query_preserves_legacy_positional_argument_order():
    within = SemanticAncestorConstraint(
        control_type="pane",
        automation_id="FORM",
    )
    query = SemanticTargetQuery(
        "edit",
        "Szerokość",
        "1000",
        within,
        "Legacy positional query",
    )

    assert query.role == "edit"
    assert query.label == "Szerokość"
    assert query.automation_id == "1000"
    assert query.within is within
    assert query.description == "Legacy positional query"
    assert query.uia_runtime_id is None
