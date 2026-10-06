from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from app.agent.agent_action import AgentAction
from app.agent.agent_intent import AgentIntent
from app.agent.agent_request import AgentRequest
from app.agent.learning.learned_workflow import LearnedWorkflow
from app.agent.learning.semantic_transition import SemanticTransition
from app.agent.planning.action_plan import ActionPlan
from app.agent.planning.action_step import ActionStep
from app.agent.runtime.action_step_result import ActionStepResult
from app.agent.runtime.action_step_status import ActionStepStatus
from app.agent.runtime.execution_context import ExecutionContext
from app.agent.verification.expected_outcome import ExpectedOutcome


@dataclass(frozen=True)
class LearnedWorkflowReplayResult:
    """Result of executing one learned semantic workflow."""

    workflow: LearnedWorkflow
    success: bool
    completed_steps: int
    total_steps: int
    control_loop_result: object

    @property
    def failed_steps(self) -> int:
        return max(
            0,
            self.total_steps - self.completed_steps,
        )


class LearnedWorkflowReplayer:
    """
    Replays a learned workflow through the normal Universal Agent control loop.

    The workflow remains semantic: no recorded coordinates, HWNDs or runtime
    identifiers are passed into execution. Each learned action becomes a
    normal AgentAction and therefore goes through the same observation,
    target resolution, safety checks, execution and verification pipeline as
    any other agent plan.
    """

    def __init__(
        self,
        *,
        control_loop,
    ) -> None:
        self.control_loop = control_loop

    def build_plan(
        self,
        workflow: LearnedWorkflow,
        *,
        confidence: float = 0.99,
    ) -> ActionPlan:
        if not workflow.steps:
            raise ValueError("Cannot replay a workflow without steps.")

        actions = []
        for step in workflow.steps:
            learned_action = step.action

            if not learned_action.name:
                raise ValueError(
                    f"Workflow step {step.index} has no action name."
                )

            actions.append(
                ActionStep(
                    index=step.index,
                    action=AgentAction(
                        name=learned_action.name,
                        description=(
                            learned_action.description
                            or f"Replay learned action "
                            f"'{learned_action.name}'."
                        ),
                        target=learned_action.target,
                        value=learned_action.value,
                        requires_environment_observation=True,
                    ),
                )
            )

        return ActionPlan(
            intent=AgentIntent.OBSERVE_WORKFLOW,
            steps=tuple(actions),
            confidence=confidence,
        )

    def replay(
        self,
        workflow: LearnedWorkflow,
        *,
        request_message: str | None = None,
    ) -> LearnedWorkflowReplayResult:
        request = AgentRequest(
            message=(
                request_message.strip()
                if isinstance(request_message, str)
                and request_message.strip()
                else workflow.trigger
            ),
            metadata={
                "learned_workflow_id": workflow.workflow_id,
                "learned_workflow_name": workflow.name,
                "replay": True,
            },
        )

        context = ExecutionContext(request=request)

        all_step_results = []
        step_results_by_run = []
        completed_steps = 0

        try:
            initial_scene = self.control_loop.observe_scene()
            context.update_scene(initial_scene)
        except AttributeError:
            # Keep lightweight/fake control loops usable in tests and legacy
            # integrations that only expose run().
            initial_scene = context.current_scene

        for step in workflow.steps:
            before_error = self._before_state_mismatch(
                step.before,
                context.current_scene,
            )
            if before_error is not None:
                failure = ActionStepResult(
                    action_name=step.action.name,
                    status=ActionStepStatus.STOPPED,
                    reason=before_error,
                )
                all_step_results.append(failure)
                break

            transition = SemanticTransition.from_snapshots(
                step.before,
                step.after,
            )

            context.set_value(
                "expected_outcomes",
                {
                    step.action.name: ExpectedOutcome(
                        description=(
                            "Verify the compact semantic state learned "
                            "after this workflow action."
                        ),
                        expected_active_application=transition.application,
                        expected_window_title=transition.window_title,
                        expected_semantic_elements=(
                            transition.requirements
                        ),
                    )
                },
            )

            single_step_plan = ActionPlan(
                intent=AgentIntent.OBSERVE_WORKFLOW,
                steps=(
                    ActionStep(
                        index=step.index,
                        action=AgentAction(
                            name=step.action.name,
                            description=(
                                step.action.description
                                or f"Replay learned action "
                                f"'{step.action.name}'."
                            ),
                            target=step.action.target,
                            value=step.action.value,
                            requires_environment_observation=True,
                        ),
                    ),
                ),
                confidence=0.99,
            )

            last_result = self.control_loop.run(
                single_step_plan,
                context,
            )

            step_results = tuple(
                getattr(last_result, "step_results", ()) or ()
            )
            all_step_results.extend(step_results)
            step_results_by_run.append(last_result)

            if not bool(getattr(last_result, "success", False)):
                break

            completed_steps += 1

        success = (
            completed_steps == len(workflow.steps)
            and len(workflow.steps) > 0
            and all(
                getattr(result, "success", False)
                for result in step_results_by_run
            )
        )

        summary = type(
            "LearnedWorkflowReplayControlLoopSummary",
            (),
            {
                "step_results": tuple(all_step_results),
                "success": success,
                "runs": tuple(step_results_by_run),
            },
        )()

        return LearnedWorkflowReplayResult(
            workflow=workflow,
            success=success,
            completed_steps=completed_steps,
            total_steps=len(workflow.steps),
            control_loop_result=summary,
        )

    @staticmethod
    def _before_state_mismatch(
        snapshot,
        scene,
    ) -> str | None:
        if snapshot is None or scene is None:
            return None

        state = scene.observation.state

        for expected, actual, label in (
            (
                snapshot.application,
                state.active_application,
                "application",
            ),
            (
                snapshot.window_title,
                state.active_window_title,
                "window title",
            ),
        ):
            if (
                isinstance(expected, str)
                and expected.strip()
                and (
                    not isinstance(actual, str)
                    or actual.strip().casefold()
                    != expected.strip().casefold()
                )
            ):
                return (
                    f"Learned BEFORE {label} does not match the "
                    f"current environment: expected "
                    f"{expected!r}, got {actual!r}."
                )

        if (
            isinstance(snapshot.active_document, str)
            and snapshot.active_document.strip()
            and scene.active_document
            and (
                scene.active_document.strip().casefold()
                != snapshot.active_document.strip().casefold()
            )
        ):
            return (
                "Learned BEFORE active document does not match "
                f"the current environment: expected "
                f"{snapshot.active_document!r}, got "
                f"{scene.active_document!r}."
            )

        return None

    @staticmethod
    def _transition_requirements(
        before,
        after,
    ) -> tuple[dict[str, object], ...]:
        return SemanticTransition.from_snapshots(
            before,
            after,
        ).requirements

    @staticmethod
    def load_json(
        path: str | Path,
    ) -> LearnedWorkflow:
        workflow_path = Path(path)

        payload = json.loads(
            workflow_path.read_text(encoding="utf-8")
        )

        if not isinstance(payload, dict):
            raise ValueError(
                "Learned workflow JSON must contain an object."
            )

        return LearnedWorkflow.from_payload(payload)
