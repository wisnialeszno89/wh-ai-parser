from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from app.agent.agent_action import AgentAction
from app.agent.agent_intent import AgentIntent
from app.agent.agent_request import AgentRequest
from app.agent.learning.learned_workflow import LearnedWorkflow
from app.agent.planning.action_plan import ActionPlan
from app.agent.planning.action_step import ActionStep
from app.agent.runtime.execution_context import ExecutionContext


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
            raise ValueError(
                "Cannot replay a workflow without steps."
            )

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
        plan = self.build_plan(workflow)

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

        context = ExecutionContext(
            request=request,
        )

        result = self.control_loop.run(
            plan,
            context,
        )

        completed_steps = sum(
            1
            for step_result in result.step_results
            if getattr(
                getattr(step_result, "status", None),
                "value",
                None,
            ) == "completed"
        )

        return LearnedWorkflowReplayResult(
            workflow=workflow,
            success=bool(result.success),
            completed_steps=completed_steps,
            total_steps=len(workflow.steps),
            control_loop_result=result,
        )

    @staticmethod
    def load_json(
        path: str | Path,
    ) -> LearnedWorkflow:
        workflow_path = Path(path)

        payload = json.loads(
            workflow_path.read_text(
                encoding="utf-8",
            )
        )

        if not isinstance(payload, dict):
            raise ValueError(
                "Learned workflow JSON must contain an object."
            )

        return LearnedWorkflow.from_payload(payload)
