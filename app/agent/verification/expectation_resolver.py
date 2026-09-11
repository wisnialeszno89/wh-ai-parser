from app.agent.agent_action import AgentAction

from app.agent.runtime.execution_context import (
    ExecutionContext,
)

from app.agent.verification.expected_outcome import (
    ExpectedOutcome,
)


class ExpectationResolver:
    """
    Resolves an expected observable outcome for an action.

    The resolver intentionally returns None when an action
    does not require environment verification.

    This keeps semantic and abstract actions independent from
    GUI-specific expectations.

    Environment-specific implementations may later extend or
    replace these expectations.
    """

    def resolve(
        self,
        action: AgentAction,
        context: ExecutionContext,
    ) -> ExpectedOutcome | None:

        expectation = self._resolve_from_context(
            action,
            context,
        )

        if expectation is not None:
            return expectation

        return self._resolve_default(
            action
        )

    def _resolve_from_context(
        self,
        action: AgentAction,
        context: ExecutionContext,
    ) -> ExpectedOutcome | None:
        """
        Resolve an explicitly registered expectation from
        the execution context.

        The context allows environment-specific executors or
        future planners to provide precise expectations without
        coupling this resolver to a specific application.
        """

        expectations = context.get_value(
            "expected_outcomes"
        )

        if not isinstance(
            expectations,
            dict,
        ):
            return None

        expectation = expectations.get(
            action.name
        )

        if isinstance(
            expectation,
            ExpectedOutcome,
        ):
            return expectation

        return None

    def _resolve_default(
        self,
        action: AgentAction,
    ) -> ExpectedOutcome | None:
        """
        Resolve built-in expectations for generic actions.

        Abstract agent actions currently do not require a GUI
        verification outcome, therefore they return None.

        Specific environments may provide richer expectations
        through the execution context.
        """

        return None
