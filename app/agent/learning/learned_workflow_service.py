from __future__ import annotations

from dataclasses import dataclass, field
from collections.abc import Callable, Mapping

from app.agent.agent_request import AgentRequest
from app.agent.learning.learned_parameter import LearnedParameterBinder
from app.agent.learning.learned_workflow_replayer import (
    LearnedWorkflowReplayResult,
    LearnedWorkflowReplayer,
)
from app.agent.learning.workflow_matcher import (
    WorkflowMatch,
    WorkflowMatcher,
)
from app.agent.learning.workflow_memory_store import WorkflowMemoryStore


@dataclass(frozen=True)
class LearnedWorkflowExecutionResult:
    """Resolution and replay result for one learned procedure."""

    match: WorkflowMatch
    replay: LearnedWorkflowReplayResult
    parameters: Mapping[str, object] = field(
        default_factory=dict
    )


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

        if matches:
            match = matches[0]
        else:
            candidate_matches = self.memory_store.match(
                request.message,
                application=application,
                limit=5,
                min_score=0.90,
            )
            match = self._select_parameterized_continuation(
                request,
                candidate_matches,
            )

        if match is None or not match.workflow.steps:
            return None

        parameters = self._resolve_parameters(
            request,
            match.workflow,
        )

        replayer = LearnedWorkflowReplayer(
            control_loop=self.control_loop,
        )

        if parameters:
            replay = replayer.replay(
                match.workflow,
                request_message=request.message,
                parameters=parameters,
            )
        else:
            replay = replayer.replay(
                match.workflow,
                request_message=request.message,
            )

        return LearnedWorkflowExecutionResult(
            match=match,
            replay=replay,
            parameters=parameters,
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

    @staticmethod
    def _select_parameterized_continuation(
        request: AgentRequest,
        candidates: tuple[WorkflowMatch, ...],
    ) -> WorkflowMatch | None:
        """
        Allow a parameterized learned workflow to accept a request that starts
        with its exact trigger and supplies all learned parameters.

        This is intentionally narrower than generic fuzzy matching.
        """
        binder = LearnedParameterBinder()
        normalized_message = WorkflowMatcher._normalize(
            request.message
        )

        for candidate in candidates:
            workflow = candidate.workflow
            if not any(
                step.action.value_source == "parameter"
                and bool(step.action.parameter_name)
                for step in workflow.steps
            ):
                continue

            trigger = WorkflowMatcher._normalize(
                workflow.trigger
            )
            if (
                not trigger
                or normalized_message == trigger
                or not normalized_message.startswith(
                    trigger + " "
                )
            ):
                continue

            # Parameter resolution is performed here so an otherwise similar
            # workflow cannot fire merely because its trigger is a prefix.
            explicit = request.metadata.get("learned_parameters")
            parameters = (
                dict(explicit)
                if isinstance(explicit, Mapping)
                else {}
            )

            if not parameters:
                continue

            parameterized_actions = tuple(
                step.action
                for step in workflow.steps
                if (
                    step.action.value_source == "parameter"
                    and step.action.parameter_name
                )
            )

            if all(
                binder.has_parameter(
                    action,
                    parameters,
                )
                for action in parameterized_actions
            ):
                return candidate

        return None
