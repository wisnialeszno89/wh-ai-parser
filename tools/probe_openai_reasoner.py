from app.agent.environment.environment_observation import (
    EnvironmentObservation,
)
from app.agent.environment.environment_state import (
    EnvironmentState,
)
from app.agent.perception.screen_scene import ScreenScene
from app.agent.reasoning.openai_plan_reasoner import (
    OpenAIPlanReasoner,
)
from app.agent.reasoning.replanning_context import (
    ReplanningActionSnapshot,
    ReplanningContext,
)


def main() -> int:
    observation = EnvironmentObservation(
        state=EnvironmentState(
            active_application="WindowHelper",
            active_window_title="WindowHelper - Quote",
            screen_width=1920,
            screen_height=1080,
        )
    )

    context = ReplanningContext(
        request_message=(
            "Przygotuj ofertę i kontynuuj, "
            "ale oczekiwany element nie pojawił się."
        ),
        intent="create_quote",
        active_plan=(
            ReplanningActionSnapshot(
                name="prepare_quote",
                description=(
                    "Prepare quotation workflow "
                    "for controlled execution."
                ),
                requires_confirmation=True,
            ),
        ),
        failed_action_name="prepare_quote",
        failed_action_description=(
            "Prepare quotation workflow "
            "for controlled execution."
        ),
        attempt_number=1,
        execution_success=True,
        execution_message="Action executed.",
        verification_verified=False,
        verification_reason="Expected element was not found.",
        verification_confidence=0.9,
        verification_metadata={
            "expected_label": "Zapisz",
            "found": False,
        },
        scene=ScreenScene(
            observation=observation,
            metadata={},
        ),
    )

    proposal = OpenAIPlanReasoner().reason(
        context
    )

    if proposal is None:
        print(
            "No reasoning proposal was returned "
            "(provider error, refusal, or invalid output)."
        )
        return 1

    print("Reasoning proposal:")
    print(f"confidence={proposal.confidence}")
    print(
        "requires_manual_review="
        f"{proposal.requires_manual_review}"
    )
    print(f"rationale={proposal.rationale}")

    for index, action in enumerate(
        proposal.actions,
        start=1,
    ):
        print(
            f"{index}. {action.name} | "
            f"{action.description} | "
            f"confirmation={action.requires_confirmation}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
