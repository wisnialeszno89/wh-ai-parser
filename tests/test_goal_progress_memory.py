"""Pure offline tests for the goal-agnostic progress supervisor."""
from types import SimpleNamespace as NS
from app.agent.runtime.goal_progress_memory import (
    ProgressMemory, action_identity, compact_state,
)


def scene(value="1000", *, stage="Wielkość okna", visible=True):
    element = NS(kind="edit", label="Szerokość", metadata={
        "source": "windowhub_ui_automation",
        "uia_visible": visible,
        "automation_id": "1000",
        "uia_runtime_id": "private-31",
        "current_value": value,
        "uia_selected": None, "uia_checked": None,
    })
    return NS(observation=NS(state=NS(
        active_application="Okna.exe", active_window_title=stage,
    )), elements=(element,))


def action(value="1500"):
    return NS(
        name="write_text", value=value,
        target=NS(automation_id="1000", role="edit")
    )


def test_detects_field_value_change_without_exposing_value():
    before, after = scene("1000"), scene("1500")
    assert compact_state(before) != compact_state(after)
    assert "1000" not in repr(compact_state(before))
    memory = ProgressMemory()
    first = memory.observe(before, stage="dimensions")
    assert first["world_changed_since_last"] is None
    second = memory.observe(after, stage="dimensions")
    assert second["world_changed_since_last"] is True
    assert second["world_observed_changes"] == 1


def test_prevents_repeated_unchanged_action_but_allows_after_state_change():
    memory = ProgressMemory()
    original = scene()
    assert memory.allow_action(action(), original, stage="dimensions")[0] is True
    assert memory.allow_action(action(), original, stage="dimensions")[0] is False
    assert memory.allow_action(action(), scene("1500"), stage="dimensions")[0] is True
    assert memory.allow_action(action("1400"), original, stage="dimensions")[0] is True


def test_action_signature_does_not_log_input_value():
    assert "1500" not in repr(action_identity(action("1500")))


def test_stage_change_counts_as_progress():
    memory = ProgressMemory()
    memory.observe(scene(), stage="dimensions")
    result = memory.observe(scene(stage="Podstawowe parametry okna"), stage="basic_parameters")
    assert result["world_changed_since_last"] is True


def test_hidden_controls_excluded_from_signature():
    assert compact_state(scene(visible=False))[-1] == ()
