from app.agent.reasoning.deterministic_plan_reasoner import (
    DeterministicPlanReasoner,
)
from app.agent.reasoning.replanning_context import (
    ReplanningActionSnapshot,
    ReplanningContext,
)


def create_context(reason):
    return ReplanningContext(
        request_message="Test request",
        intent="create_quote",
        active_plan=(
            ReplanningActionSnapshot(
                name="failed_action",
                description="Previous action.",
                requires_confirmation=False,
            ),
        ),
        failed_action_name="failed_action",
        failed_action_description="Previous action.",
        attempt_number=1,
        execution_success=True,
        execution_message="Executed.",
        verification_verified=False,
        verification_reason=reason,
        verification_confidence=0.9,
        verification_metadata={
            "found": False,
        },
    )


def test_deterministic_reasoner_recovers_missing_element():
    reasoner = DeterministicPlanReasoner()

    proposal = reasoner.reason(
        create_context(
            "Expected element was not found."
        )
    )

    assert proposal is not None
    assert proposal.confidence == 0.7
    assert [
        action.name
        for action in proposal.actions
    ] == [
        "refresh_current_context",
        "retry_semantic_workflow",
    ]


def test_deterministic_reasoner_declines_unknown_failure():
    reasoner = DeterministicPlanReasoner()

    proposal = reasoner.reason(
        create_context(
            "An unknown verification failure occurred."
        )
    )

    assert proposal is None
