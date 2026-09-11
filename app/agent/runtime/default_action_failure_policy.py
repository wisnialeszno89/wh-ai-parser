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

    The runtime must never silently continue after a failure
    unless a more specific policy explicitly allows it.
    """

    def decide(
        self,
        action: AgentAction,
        result: ExecutionLoopResult,
        context: ExecutionContext,
    ) -> ActionFailureDecision:

        if result.requires_manual_review:
            return (
                ActionFailureDecision.MANUAL_REVIEW
            )

        if result.stopped:
            return (
                ActionFailureDecision.STOP
            )

        return ActionFailureDecision.STOP
