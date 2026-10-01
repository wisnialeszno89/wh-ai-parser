from app.agent.reasoning.openai_task_reasoner import (
    OpenAITaskReasoner,
    OpenAITaskReasonerConfig,
    _OpenAITaskReasoningAction,
    _OpenAITaskReasoningProposal,
)
from app.agent.reasoning.task_planning_context import (
    TaskPlanningContext,
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
    return TaskPlanningContext(
        request_message="Otwórz nową ofertę",
        intent="execute_in_wh",
        capability_name="WH_WINDOW",
        capability_description="Controlled WindowHub execution.",
        skill_name="WHWindowSkill",
    )


def create_config():
    return OpenAITaskReasonerConfig(
        api_key="test-key",
        model="gpt-5.6-luna",
    )


def test_openai_task_reasoner_maps_structured_response():
    parsed = _OpenAITaskReasoningProposal(
        actions=(
            _OpenAITaskReasoningAction(
                name="click_screen_element",
                description="Click the requested semantic control.",
                target="NOWA OFERTA",
            ),
        ),
        rationale="Open the new offer workflow.",
        confidence=0.94,
        requires_manual_review=False,
    )

    client = FakeClient(parsed)

    reasoner = OpenAITaskReasoner(
        config=create_config(),
        client=client,
    )

    proposal = reasoner.reason(
        create_context()
    )

    assert proposal is not None
    assert proposal.confidence == 0.94
    assert proposal.actions[0].name == (
        "click_screen_element"
    )
    assert proposal.actions[0].target == (
        "NOWA OFERTA"
    )

    call = client.responses.calls[0]

    assert call["model"] == "gpt-5.6-luna"
    assert call["text_format"].__name__ == (
        "_OpenAITaskReasoningProposal"
    )


def test_openai_task_reasoner_fails_closed_on_provider_error():
    class BrokenResponses:

        def parse(self, **kwargs):
            raise RuntimeError(
                "Provider unavailable."
            )

    class BrokenClient:
        responses = BrokenResponses()

    reasoner = OpenAITaskReasoner(
        config=create_config(),
        client=BrokenClient(),
    )

    assert reasoner.reason(
        create_context()
    ) is None


def test_openai_task_reasoner_guides_ready_workflow_to_gui_action():
    context = TaskPlanningContext(
        request_message="Przygotuj tę ofertę",
        intent="create_quote",
        capability_name="WH_WINDOW",
        capability_description="Controlled WindowHub execution.",
        skill_name="WHWindowSkill",
        offer_workflow={
            "workflow_state": "ready_for_pricing",
            "is_ready_for_pricing": True,
            "requires_salesperson_input": False,
            "questions": (),
            "missing_fields": (),
            "conflicts": (),
            "offer_context": {
                "product_type": "window",
                "width": 1230,
                "height": 1480,
            },
        },
    )

    parsed = _OpenAITaskReasoningProposal(
        actions=(
            _OpenAITaskReasoningAction(
                name="click_screen_element",
                description="Continue the visible quotation workflow.",
                target="Przelicz",
            ),
        ),
        rationale="The offer data is complete and the visible pricing control is the next step.",
        confidence=0.93,
        requires_manual_review=False,
    )

    client = FakeClient(parsed)

    reasoner = OpenAITaskReasoner(
        config=create_config(),
        client=client,
    )

    proposal = reasoner.reason(context)

    assert proposal is not None
    assert proposal.actions[0].name == "click_screen_element"
    assert proposal.actions[0].target == "Przelicz"

    instructions = client.responses.calls[0]["instructions"]

    assert "READY_FOR_PRICING" in instructions
    assert "Do NOT return analyze_request" in instructions
    assert "next safe user-visible GUI action" in instructions
