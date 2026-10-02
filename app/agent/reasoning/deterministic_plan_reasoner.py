from app.agent.reasoning.plan_reasoner import (
    PlanReasoner,
)

from app.agent.reasoning.replanning_context import (
    ReplanningContext,
)

from app.agent.reasoning.reasoning_action import (
    ReasoningAction,
)

from app.agent.reasoning.reasoning_proposal import (
    ReasoningProposal,
)


class DeterministicPlanReasoner(
    PlanReasoner
):
    """
    Provider-neutral deterministic fallback reasoner.

    This is intentionally conservative. It demonstrates the
    complete reasoning contract without introducing an external
    model or network dependency.

    It only reasons from structured verification failures and
    emits semantic recovery actions.
    """

    def reason(
        self,
        context: ReplanningContext,
    ) -> ReasoningProposal | None:

        reason = (
            context.verification_reason
            .strip()
            .casefold()
        )

        if "expected element was not found" in reason:
            return ReasoningProposal(
                actions=(
                    ReasoningAction(
                        name="refresh_current_context",
                        description=(
                            "Refresh the current application context "
                            "and reassess the available workflow state."
                        ),
                    ),
                    ReasoningAction(
                        name="retry_semantic_workflow",
                        description=(
                            "Retry the failed semantic workflow using "
                            "the refreshed context."
                        ),
                    ),
                ),
                rationale=(
                    "The expected target was not observed. "
                    "Refresh the semantic context before retrying."
                ),
                confidence=0.7,
            )

        return None
