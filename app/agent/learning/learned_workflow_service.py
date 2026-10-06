from __future__ import annotations

from dataclasses import dataclass

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

    Exact or near-exact trigger matches are intentionally required for this
    first execution bridge. Parameter adaptation and fuzzy intent expansion
    will be added only after learned workflow execution is stable.
    """

    def __init__(
        self,
        *,
        memory_store: WorkflowMemoryStore,
        control_loop,
        min_score: float = 0.99,
    ) -> None:
        if not 0.0 <= min_score <= 1.0:
            raise ValueError("min_score must be between 0 and 1.")

        self.memory_store = memory_store
        self.control_loop = control_loop
        self.min_score = min_score

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
        replay = LearnedWorkflowReplayer(
            control_loop=self.control_loop,
        ).replay(
            match.workflow,
            request_message=request.message,
        )

        return LearnedWorkflowExecutionResult(
            match=match,
            replay=replay,
        )
