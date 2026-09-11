from app.agent.agent_action import AgentAction

from app.agent.decision.decision import (
    Decision,
)

from app.agent.decision.decision_type import (
    DecisionType,
)

from app.agent.runtime.execution_context import (
    ExecutionContext,
)


class DecisionEngine:
    """
    Conservative decision layer for controlled execution.

    The engine decides whether an action may proceed based on
    the current execution context and perceived environment.

    It supports both:

    - ExecutionContext
    - AgentExecutionContext
    """

    def decide(
        self,
        action: AgentAction,
        context: ExecutionContext,
    ) -> Decision:
        """
        Decide whether execution can proceed safely.

        Decision priority:

        1. Explicit semantic manual review requirement.
        2. Action requiring confirmation.
        3. Unexpected dialogs in the perceived scene.
        4. Otherwise proceed.
        """

        requires_manual_review = getattr(
            context,
            "requires_manual_review",
            False,
        )

        if requires_manual_review:
            return Decision(
                decision_type=(
                    DecisionType.MANUAL_REVIEW
                ),
                reason=(
                    "Execution context requires "
                    "manual review."
                ),
                requires_manual_review=True,
            )

        if action.requires_confirmation:
            return Decision(
                decision_type=(
                    DecisionType.MANUAL_REVIEW
                ),
                reason=(
                    "Action requires explicit "
                    "confirmation."
                ),
                requires_manual_review=True,
            )

        scene = getattr(
            context,
            "current_scene",
            None,
        )

        if scene is not None:

            dialogs = scene.elements_of_kind(
                "dialog"
            )

            if dialogs:

                dialog = dialogs[0]

                return Decision(
                    decision_type=(
                        DecisionType.MANUAL_REVIEW
                    ),
                    target=dialog.label,
                    reason=(
                        "Dialog detected in environment."
                    ),
                    requires_manual_review=True,
                    metadata={
                        "element_kind": dialog.kind,
                        "dialog_count": len(dialogs),
                    },
                )

        return Decision(
            decision_type=DecisionType.PROCEED,
            reason=(
                "No execution blocker detected."
            ),
        )
