from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Callable, Mapping

from app.agent.agent_request import AgentRequest
from app.agent.learning.learned_workflow_replayer import (
    LearnedWorkflowReplayResult,
    LearnedWorkflowReplayer,
)
from app.agent.learning.workflow_matcher import WorkflowMatch
from app.agent.learning.workflow_memory_store import WorkflowMemoryStore


@dataclass(frozen=True)
class LearnedWorkflowExecutionResult:
    """Resolution and replay result for one learned procedure."""

    match: WorkflowMatch
    replay: LearnedWorkflowReplayResult


class LearnedWorkflowService:
    """Resolve an explicit learned procedure and replay it safely.

    Exact trigger matching remains the execution gate. Request-time
    parameters can override parameterized text-entry values without changing
    the stored workflow.
    """

    def __init__(
        self,
        *,
        memory_store: WorkflowMemoryStore,
        control_loop,
        min_score: float = 0.99,
        parameter_resolver: Callable[[AgentRequest, object], Mapping[str, object]] | None = None,
    ) -> None:
        if not 0.0 <= min_score <= 1.0:
            raise ValueError("min_score must be between 0 and 1.")

        self.memory_store = memory_store
        self.control_loop = control_loop
        self.min_score = min_score
        self.parameter_resolver = parameter_resolver

    def execute(
        self,
        request: AgentRequest,
        *,
        application: str | None = None,
    ) -> LearnedWorkflowExecutionResult | None:
        matches = self.memory_store.match(
            request.message,
            application=application,
            limit=1,
            min_score=self.min_score,
        )

        if not matches:
            return None

        match = matches[0]
        if not match.workflow.steps:
            return None

        parameters = self._resolve_parameters(
            request,
            match.workflow,
        )

        replay = LearnedWorkflowReplayer(
            control_loop=self.control_loop,
        ).replay(
            match.workflow,
            request_message=request.message,
            parameters=parameters,
        )

        return LearnedWorkflowExecutionResult(
            match=match,
            replay=replay,
        )

    def _resolve_parameters(
        self,
        request: AgentRequest,
        workflow,
    ) -> Mapping[str, object]:
        explicit = request.metadata.get("learned_parameters")
        if isinstance(explicit, Mapping):
            return dict(explicit)

        if self.parameter_resolver is None:
            return {}

        resolved = self.parameter_resolver(
            request,
            workflow,
        )

        if isinstance(resolved, Mapping):
            return dict(resolved)

        return {}
