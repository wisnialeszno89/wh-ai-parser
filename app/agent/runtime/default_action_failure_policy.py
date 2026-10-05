from app.agent.agent_action import (
    AgentAction,
)

from app.agent.runtime.action_failure_decision import (
    ActionFailureDecision,
)

from app.agent.runtime.action_failure_policy import (
    ActionFailurePolicy,
)

from app.agent.runtime.execution_context import (
    ExecutionContext,
)

from app.agent.runtime.execution_loop_result import (
    ExecutionLoopResult,
)


class DefaultActionFailurePolicy(
    ActionFailurePolicy
):
    """
    Conservative default failure policy.

    The runtime never silently continues after a failure unless the
    action explicitly allows skipping. Recovery/replanning is handled
    before this policy is consulted.
    """

    def decide(
        self,
        action: AgentAction,
        result: ExecutionLoopResult,
        context: ExecutionContext,
    ) -> ActionFailureDecision:

        # A safety/manual-review condition must never be bypassed by
        # the optional-action mechanism.
        if result.requires_manual_review:
            return (
                ActionFailureDecision.MANUAL_REVIEW
            )

        if action.allow_skip_on_failure:
            return (
                ActionFailureDecision.SKIP
            )

        if result.stopped:
            return (
                ActionFailureDecision.STOP
            )

        return ActionFailureDecision.STOP
