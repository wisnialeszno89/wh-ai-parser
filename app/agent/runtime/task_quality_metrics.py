from dataclasses import dataclass

from app.agent.runtime.action_step_status import ActionStepStatus


@dataclass(frozen=True)
class TaskQualityMetrics:
    """Evidence-based quality metrics for one autonomous task run."""

    terminal_steps: int = 0
    verified_actions: int = 0
    first_pass_verified_actions: int = 0
    recovered_actions: int = 0
    failed_steps: int = 0
    skipped_steps: int = 0
    manual_review_steps: int = 0
    stopped_steps: int = 0
    replans: int = 0

    task_completed: bool = False
    task_success: bool = False
    quality_state: str = "incomplete"

    def __post_init__(self) -> None:
        for field_name in (
            "terminal_steps",
            "verified_actions",
            "first_pass_verified_actions",
            "recovered_actions",
            "failed_steps",
            "skipped_steps",
            "manual_review_steps",
            "stopped_steps",
            "replans",
        ):
            if getattr(self, field_name) < 0:
                raise ValueError(
                    f"{field_name} must be non-negative."
                )

        if (
            self.verified_actions
            > self.terminal_steps
        ):
            raise ValueError(
                "verified_actions cannot exceed terminal_steps."
            )

        if (
            self.first_pass_verified_actions
            + self.recovered_actions
            > self.verified_actions
        ):
            raise ValueError(
                "first_pass_verified_actions + recovered_actions "
                "cannot exceed verified_actions."
            )

        if self.task_success and not self.task_completed:
            raise ValueError(
                "task_success requires task_completed."
            )

        if self.quality_state not in {
            "completed",
            "completed_with_recovery",
            "manual_review",
            "failed",
            "stopped",
            "incomplete",
        }:
            raise ValueError(
                "Unsupported quality_state."
            )

    @property
    def verification_success_rate(self) -> float:
        if self.terminal_steps == 0:
            return 0.0
        return self.verified_actions / self.terminal_steps

    @property
    def first_pass_success_rate(self) -> float:
        if self.verified_actions == 0:
            return 0.0
        return (
            self.first_pass_verified_actions
            / self.verified_actions
        )

    @property
    def recovery_rate(self) -> float:
        if self.verified_actions == 0:
            return 0.0
        return self.recovered_actions / self.verified_actions

    @property
    def replan_rate(self) -> float:
        if self.terminal_steps == 0:
            return 0.0
        return self.replans / self.terminal_steps

    def to_payload(self) -> dict[str, object]:
        return {
            "terminal_steps": self.terminal_steps,
            "verified_actions": self.verified_actions,
            "first_pass_verified_actions": (
                self.first_pass_verified_actions
            ),
            "recovered_actions": self.recovered_actions,
            "failed_steps": self.failed_steps,
            "skipped_steps": self.skipped_steps,
            "manual_review_steps": self.manual_review_steps,
            "stopped_steps": self.stopped_steps,
            "replans": self.replans,
            "verification_success_rate": (
                self.verification_success_rate
            ),
            "first_pass_success_rate": (
                self.first_pass_success_rate
            ),
            "recovery_rate": self.recovery_rate,
            "replan_rate": self.replan_rate,
            "task_completed": self.task_completed,
            "task_success": self.task_success,
            "quality_state": self.quality_state,
        }


def quality_metrics_from_results(
    *,
    completed: bool,
    success: bool,
    requires_manual_review: bool,
    stopped: bool,
    step_results,
) -> TaskQualityMetrics:
    terminal_steps = 0
    verified_actions = 0
    first_pass_verified_actions = 0
    recovered_actions = 0
    failed_steps = 0
    skipped_steps = 0
    manual_review_steps = 0
    stopped_steps = 0
    replans = 0

    for result in step_results:
        control = result.control_loop_result
        if control is None:
            continue

        replans += len(
            getattr(control, "replan_records", ())
        )

        for step in getattr(control, "step_results", ()):
            status = step.status
            if status in {
                ActionStepStatus.COMPLETED,
                ActionStepStatus.FAILED,
                ActionStepStatus.SKIPPED,
                ActionStepStatus.MANUAL_REVIEW,
                ActionStepStatus.STOPPED,
            }:
                terminal_steps += 1

            if status == ActionStepStatus.COMPLETED:
                verified_actions += 1
                attempts = max(
                    int(getattr(step, "attempts", 0)),
                    0,
                )
                if attempts <= 1:
                    first_pass_verified_actions += 1
                else:
                    recovered_actions += 1

            elif status == ActionStepStatus.FAILED:
                failed_steps += 1
            elif status == ActionStepStatus.SKIPPED:
                skipped_steps += 1
            elif status == ActionStepStatus.MANUAL_REVIEW:
                manual_review_steps += 1
            elif status == ActionStepStatus.STOPPED:
                stopped_steps += 1

    if completed and success and not requires_manual_review:
        quality_state = (
            "completed_with_recovery"
            if recovered_actions > 0 or replans > 0
            else "completed"
        )
    elif requires_manual_review:
        quality_state = "manual_review"
    elif stopped:
        quality_state = "stopped"
    elif failed_steps > 0:
        quality_state = "failed"
    else:
        quality_state = "incomplete"

    return TaskQualityMetrics(
        terminal_steps=terminal_steps,
        verified_actions=verified_actions,
        first_pass_verified_actions=first_pass_verified_actions,
        recovered_actions=recovered_actions,
        failed_steps=failed_steps,
        skipped_steps=skipped_steps,
        manual_review_steps=manual_review_steps,
        stopped_steps=stopped_steps,
        replans=replans,
        task_completed=completed,
        task_success=(
            completed
            and success
            and not requires_manual_review
        ),
        quality_state=quality_state,
    )
