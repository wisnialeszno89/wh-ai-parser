from app.agent.runtime.task_quality_metrics import TaskQualityMetrics


def test_quality_metrics_defaults_are_stable():
    metrics = TaskQualityMetrics()
    assert metrics.quality_state == "incomplete"
    assert metrics.verification_success_rate == 0.0


from pathlib import Path
from types import SimpleNamespace

import pytest

from app.agent.runtime.action_step_result import ActionStepResult
from app.agent.runtime.action_step_status import ActionStepStatus
from app.agent.runtime.task_quality_metrics import (
    quality_metrics_from_results,
)


def control(*steps, replan_count=0):
    return SimpleNamespace(
        step_results=steps,
        replan_records=tuple(range(replan_count)),
    )


def result_with_control(control_result):
    return SimpleNamespace(
        control_loop_result=control_result,
    )


def test_quality_metrics_distinguish_first_pass_and_recovered_actions():
    first_pass = ActionStepResult(
        action_name="browser_write_text",
        status=ActionStepStatus.COMPLETED,
        attempts=1,
    )
    recovered = ActionStepResult(
        action_name="browser_click",
        status=ActionStepStatus.COMPLETED,
        attempts=2,
    )

    result = quality_metrics_from_results(
        completed=True,
        success=True,
        requires_manual_review=False,
        stopped=False,
        step_results=(
            result_with_control(
                control(first_pass, recovered, replan_count=1)
            ),
        ),
    )

    assert result.task_completed is True
    assert result.task_success is True
    assert result.quality_state == "completed_with_recovery"
    assert result.terminal_steps == 2
    assert result.verified_actions == 2
    assert result.first_pass_verified_actions == 1
    assert result.recovered_actions == 1
    assert result.replans == 1
    assert result.verification_success_rate == pytest.approx(1.0)
    assert result.first_pass_success_rate == pytest.approx(0.5)
    assert result.recovery_rate == pytest.approx(0.5)
    assert result.replan_rate == pytest.approx(0.5)


def test_quality_metrics_record_failed_skipped_and_manual_steps():
    failed = ActionStepResult(
        action_name="browser_click",
        status=ActionStepStatus.FAILED,
        reason="step_failed",
        attempts=2,
    )
    skipped = ActionStepResult(
        action_name="browser_click",
        status=ActionStepStatus.SKIPPED,
        reason="policy_skip",
        attempts=1,
    )
    manual = ActionStepResult(
        action_name="browser_click",
        status=ActionStepStatus.MANUAL_REVIEW,
        reason="approval_required",
        attempts=0,
    )

    result = quality_metrics_from_results(
        completed=False,
        success=False,
        requires_manual_review=True,
        stopped=True,
        step_results=(
            result_with_control(
                control(failed, skipped, manual)
            ),
        ),
    )

    assert result.quality_state == "manual_review"
    assert result.terminal_steps == 3
    assert result.verified_actions == 0
    assert result.failed_steps == 1
    assert result.skipped_steps == 1
    assert result.manual_review_steps == 1
    assert result.stopped_steps == 0
    assert result.verification_success_rate == 0.0


@pytest.mark.parametrize(
    "kwargs",
    [
        {"verified_actions": 2, "terminal_steps": 1},
        {
            "verified_actions": 2,
            "first_pass_verified_actions": 2,
            "recovered_actions": 1,
        },
        {
            "task_success": True,
            "task_completed": False,
        },
    ],
)
def test_quality_metrics_reject_invalid_invariants(kwargs):
    with pytest.raises(ValueError):
        TaskQualityMetrics(**kwargs)


def test_quality_metrics_payload_is_stable():
    result = TaskQualityMetrics(
        terminal_steps=2,
        verified_actions=2,
        first_pass_verified_actions=2,
        task_completed=True,
        task_success=True,
        quality_state="completed",
    )

    payload = result.to_payload()

    assert payload["verified_actions"] == 2
    assert payload["verification_success_rate"] == 1.0
    assert payload["first_pass_success_rate"] == 1.0
    assert payload["quality_state"] == "completed"



def test_windowhub_quality_benchmark_reasoning_cost_uses_summary_payload_contract():
    source = Path("tools/live_windowhub_quality_benchmark.py").read_text(encoding="utf-8")
    assert 'cost.provider' not in source
    assert 'print(f"model={cost.model!r}")' not in source
    assert 'cost.calls' in source
    assert 'cost.models' in source
