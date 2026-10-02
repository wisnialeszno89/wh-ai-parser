from app.agent.agent_request import AgentRequest
from app.agent.environment.environment_observation import (
    EnvironmentObservation,
)
from app.agent.environment.environment_state import (
    EnvironmentState,
)
from app.agent.perception.screen_scene import ScreenScene
from app.agent.reasoning.openai_plan_reasoner import (
    OpenAIPlanReasoner,
    OpenAIPlanReasonerConfig,
)
from app.agent.reasoning.replanning_context import (
    ReplanningActionSnapshot,
    ReplanningContext,
)


class ParsedResponse:
    def __init__(self, parsed):
        self.output_parsed = parsed


class FakeResponses:

    def __init__(self, parsed):
        self.parsed = parsed
        self.calls = []

    def parse(self, **kwargs):
        self.calls.append(kwargs)
        return ParsedResponse(self.parsed)


class FakeClient:

    def __init__(self, parsed):
        self.responses = FakeResponses(parsed)


def create_context():
    observation = EnvironmentObservation(
        state=EnvironmentState(
            active_application="WindowHelper",
            active_window_title="WindowHelper - Quote",
            screen_width=1920,
            screen_height=1080,
        ),
    )

    return ReplanningContext(
        request_message="Przygotuj ofertę.",
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
        verification_reason="Expected element was not found.",
        verification_confidence=0.9,
        verification_metadata={
            "found": False,
        },
        scene=ScreenScene(
            observation=observation,
            metadata={
                "execution_runtime": {
                    "tracked_object_id": "TO-0004",
                },
            },
        ),
    )


def create_config():
    return OpenAIPlanReasonerConfig(
        api_key="test-key",
        model="gpt-5.6-luna",
    )


def test_openai_reasoner_maps_structured_response():
    from app.agent.reasoning.openai_plan_reasoner import (
        _OpenAIReasoningAction,
        _OpenAIReasoningProposal,
    )

    parsed = _OpenAIReasoningProposal(
        actions=(
            _OpenAIReasoningAction(
                name="refresh_current_context",
                description="Refresh semantic context.",
            ),
        ),
        rationale="The target was not observed.",
        confidence=0.8,
        requires_manual_review=False,
    )

    client = FakeClient(parsed)
    reasoner = OpenAIPlanReasoner(
        config=create_config(),
        client=client,
    )

    proposal = reasoner.reason(
        create_context()
    )

    assert proposal is not None
    assert proposal.confidence == 0.8
    assert proposal.rationale == (
        "The target was not observed."
    )
    assert proposal.actions[0].name == (
        "refresh_current_context"
    )

    call = client.responses.calls[0]

    assert call["model"] == "gpt-5.6-luna"
    assert call["text_format"].__name__ == (
        "_OpenAIReasoningProposal"
    )

    assert "TO-0004" not in call["input"]
    assert "execution_runtime" not in call["input"]


def test_openai_reasoner_fails_closed_on_provider_error():
    class BrokenResponses:

        def parse(self, **kwargs):
            raise RuntimeError(
                "Provider unavailable."
            )

    class BrokenClient:

        responses = BrokenResponses()

    reasoner = OpenAIPlanReasoner(
        config=create_config(),
        client=BrokenClient(),
    )

    assert reasoner.reason(
        create_context()
    ) is None
