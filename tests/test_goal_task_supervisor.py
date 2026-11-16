"""Task dependency and timed handoff policy tests."""
import pytest
from app.agent.runtime.goal_task_supervisor import (
    TaskItem, TaskLedger, TaskState, timed_salesperson_prompt,
)
from app.agent.runtime.windowhub_discovery_diagnostics import (
    categorize_window_title, suggest_recovery,
)


def test_optional_missing_detail_is_skipped_and_independent_work_continues():
    ledger = TaskLedger({
        "dimensions": TaskItem("dimensions"),
        "decorative_sill": TaskItem("decorative_sill", required=False),
        "color": TaskItem("color"),
        "review": TaskItem("review", depends_on=("dimensions", "color")),
    })
    assert ledger.ready() == ("dimensions", "decorative_sill", "color")
    assert ledger.unresolved("decorative_sill", reason="handoff_timed_out") == "skipped"
    assert ledger.ready() == ("dimensions", "color")
    ledger.verify("dimensions")
    ledger.verify("color")
    assert ledger.ready() == ("review",)
    ledger.verify("review")
    assert ledger.final_status() == "partial_requires_review"
    assert ledger.issues[0].reason == "handoff_timed_out"


def test_required_missing_dimension_blocks_dependants_but_not_independent_task():
    ledger = TaskLedger({
        "width": TaskItem("width"),
        "height": TaskItem("height"),
        "build": TaskItem("build", depends_on=("width", "height")),
        "notes": TaskItem("notes", required=False),
    })
    assert ledger.unresolved("width", reason="field_unobservable") == "blocked"
    assert ledger.state("build") is TaskState.BLOCKED
    assert ledger.ready() == ("height", "notes")
    assert ledger.final_status() == "blocked_partial"
    assert len(ledger.issues) == 2


def test_skipped_optional_dependency_still_blocks_dependent_step():
    ledger = TaskLedger({
        "optional_finish": TaskItem("optional_finish", required=False),
        "finish_calculation": TaskItem("finish_calculation", depends_on=("optional_finish",)),
        "width": TaskItem("width"),
    })
    ledger.unresolved("optional_finish", reason="operator_unavailable")
    assert ledger.state("finish_calculation") is TaskState.BLOCKED
    assert ledger.ready() == ("width",)


def test_circular_and_unknown_dependencies_rejected():
    with pytest.raises(ValueError, match="cyclic"):
        TaskLedger({
            "a": TaskItem("a", depends_on=("b",)),
            "b": TaskItem("b", depends_on=("a",)),
        })
    with pytest.raises(ValueError, match="invalid"):
        TaskLedger({"a": TaskItem("a", depends_on=("missing",))})


def test_explicit_timed_handoff_supports_timeout_and_answer():
    calls = []
    def timeout(question, seconds):
        calls.append((question, seconds))
        return None
    assert timed_salesperson_prompt("Brak potwierdzenia", timeout_seconds=60, reader=timeout) is None
    assert calls == [("Brak potwierdzenia", 60)]
    assert timed_salesperson_prompt(
        "Kontynuować?", timeout_seconds=60, reader=lambda q, t: "tak"
    ) == "tak"


def test_discovery_diagnosis_without_guessing_window_titles():
    assert categorize_window_title("Wielkość okna") == "wizard"
    assert categorize_window_title("Okna - OFR/4670-") == "document"
    assert categorize_window_title("Własne okno") == "unrecognized"
    assert suggest_recovery({"processes": 0}) == "windowhub_process_not_running"
    assert suggest_recovery({"processes": 1, "visible_titled_windows": 0}) == "no_visible_titled_window_or_application_minimized_to_tray"
    assert suggest_recovery({
        "processes": 1, "visible_titled_windows": 1, "unrecognized": 1,
    }) == "windowhub_running_but_title_not_mapped"
    assert suggest_recovery({
        "processes": 1, "visible_titled_windows": 2, "wizard": 1, "document": 1,
    }) == "multiple_workflow_windows_need_context"
