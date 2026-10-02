from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from app.agent.agent_request import AgentRequest
from app.agent.environment.environment_runtime import (
    EnvironmentRuntime,
)
from app.agent.execution.execution_engine import (
    ExecutionEngine,
)
from app.agent.perception.perception_engine import (
    PerceptionEngine,
)
from app.agent.reasoning.navimind_client import (
    NaviMindClient,
    NaviMindClientError,
)
from app.agent.reasoning.navimind_config import (
    NaviMindConfig,
)
from app.agent.reasoning.navimind_context_builder import (
    NaviMindContextBuilder,
)
from app.agent.runtime.execution_context import (
    AgentExecutionContext,
    ExecutionContext,
)


@dataclass(frozen=True)
class NaviMindLoopResult:
    task_id: str
    completed: bool
    stopped: bool
    requires_manual_review: bool
    steps: int
    message: str
    rationale: str = ""
    confidence: float = 0.0
    last_action_name: str | None = None
    metadata: dict[str, Any] = field(
        default_factory=dict
    )


class NaviMindAgentLoop:
    """
    One closed-loop bridge between the local runtime and NaviMind.

    The loop keeps all environment-specific perception/execution local:

        observe -> perceive -> NaviMind -> semantic action
          -> local execution -> re-observe

    NaviMind never receives coordinates, handles or provider IDs.
    """

    def __init__(
        self,
        environment: EnvironmentRuntime,
        perception_engine: PerceptionEngine,
        execution_engine: ExecutionEngine,
        *,
        config: NaviMindConfig | None = None,
        client: NaviMindClient | None = None,
        context_builder: NaviMindContextBuilder | None = None,
        max_steps: int = 12,
    ) -> None:
        if max_steps < 1:
            raise ValueError(
                "max_steps must be at least 1"
            )

        resolved_config = (
            config
            if config is not None
            else NaviMindConfig.from_environment()
        )

        if client is None and resolved_config is None:
            raise ValueError(
                "NAVIMIND_AGENT_URL is not configured."
            )

        self.environment = environment
        self.perception = perception_engine
        self.execution = execution_engine
        self.client = (
            client
            if client is not None
            else NaviMindClient(
                resolved_config  # type: ignore[arg-type]
            )
        )
        self.context_builder = (
            context_builder
            if context_builder is not None
            else NaviMindContextBuilder()
        )
        self.max_steps = max_steps

    def run(
        self,
        request: AgentRequest,
        *,
        execution_context: AgentExecutionContext | None = None,
    ) -> NaviMindLoopResult:
        task_id = f"wh-{uuid4().hex}"

        context = (
            execution_context
            if execution_context is not None
            else ExecutionContext(
                request=request
            )
        )

        last_action_name = None
        experience: list[dict[str, Any]] = []

        for step_number in range(
            1,
            self.max_steps + 1,
        ):
            observation = self.environment.observe()
            context.update_observation(
                observation
            )

            scene = self.perception.perceive(
                observation
            )

            context.update_scene(scene)

            task = self.context_builder.build(
                request,
                observation,
                scene,
                execution_context=(
                    execution_context
                ),
                task_id=task_id,
                experience=tuple(
                    experience
                ),
            )

            try:
                response = self.client.reason(
                    task
                )
            except NaviMindClientError as exc:
                return NaviMindLoopResult(
                    task_id=task_id,
                    completed=False,
                    stopped=True,
                    requires_manual_review=True,
                    steps=step_number - 1,
                    message=str(exc),
                    confidence=0.0,
                    last_action_name=(
                        last_action_name
                    ),
                )

            if response.status == "done":
                return NaviMindLoopResult(
                    task_id=task_id,
                    completed=True,
                    stopped=False,
                    requires_manual_review=False,
                    steps=step_number - 1,
                    message=(
                        "NaviMind reported the goal "
                        "complete."
                    ),
                    rationale=response.rationale,
                    confidence=response.confidence,
                    last_action_name=(
                        last_action_name
                    ),
                    metadata=response.metadata,
                )

            if response.status == "manual_review":
                return NaviMindLoopResult(
                    task_id=task_id,
                    completed=False,
                    stopped=True,
                    requires_manual_review=True,
                    steps=step_number - 1,
                    message=(
                        response.rationale
                        or "NaviMind requested manual review."
                    ),
                    rationale=response.rationale,
                    confidence=response.confidence,
                    last_action_name=(
                        last_action_name
                    ),
                    metadata=response.metadata,
                )

            action = self.context_builder.to_agent_action(
                response
            )

            if action is None:
                return NaviMindLoopResult(
                    task_id=task_id,
                    completed=False,
                    stopped=True,
                    requires_manual_review=True,
                    steps=step_number - 1,
                    message=(
                        "NaviMind returned no executable "
                        "semantic action."
                    ),
                    rationale=response.rationale,
                    confidence=response.confidence,
                )

            last_action_name = action.name

            if action.requires_confirmation:
                return NaviMindLoopResult(
                    task_id=task_id,
                    completed=False,
                    stopped=True,
                    requires_manual_review=True,
                    steps=step_number - 1,
                    message=(
                        "Action requires user confirmation: "
                        f"{action.description}"
                    ),
                    rationale=response.rationale,
                    confidence=response.confidence,
                    last_action_name=(
                        action.name
                    ),
                    metadata={
                        "target": action.target,
                        "value": action.value,
                    },
                )

            execution_result = (
                self.execution.execute(
                    action,
                    context,
                )
            )

            experience.append(
                {
                    "step": step_number,
                    "action": {
                        "name": action.name,
                        "description": (
                            action.description
                        ),
                    },
                    "execution": {
                        "success": (
                            execution_result.success
                        ),
                        "message": (
                            execution_result.message
                        ),
                        "requires_manual_review": (
                            execution_result
                            .requires_manual_review
                        ),
                    },
                }
            )

            if not execution_result.success:
                return NaviMindLoopResult(
                    task_id=task_id,
                    completed=False,
                    stopped=True,
                    requires_manual_review=(
                        execution_result
                        .requires_manual_review
                        or True
                    ),
                    steps=step_number,
                    message=(
                        execution_result.message
                    ),
                    rationale=response.rationale,
                    confidence=response.confidence,
                    last_action_name=(
                        action.name
                    ),
                    metadata=(
                        execution_result.metadata
                        or {}
                    ),
                )

        return NaviMindLoopResult(
            task_id=task_id,
            completed=False,
            stopped=True,
            requires_manual_review=True,
            steps=self.max_steps,
            message=(
                "NaviMind step limit reached."
            ),
            last_action_name=last_action_name,
        )
