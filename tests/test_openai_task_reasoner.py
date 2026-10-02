from app.agent.reasoning.openai_task_reasoner import (
    OpenAITaskReasoner,
    OpenAITaskReasonerConfig,
    _OpenAITaskReasoningAction,
    _OpenAITaskReasoningProposal,
)
from app.agent.reasoning.task_planning_context import (
    TaskPlanningContext,
)
from app.agent.environment.environment_observation import (
    EnvironmentObservation,
)
from app.agent.environment.environment_state import (
    EnvironmentState,
)
from app.agent.perception.screen_scene import ScreenScene
from app.wh.vision.screenshot import Screenshot
import json
import numpy as np


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
    assert "missing value" in instructions
    assert "write_text" in instructions


def test_openai_task_reasoner_maps_semantic_text_value():
    context = TaskPlanningContext(
        request_message="Wpisz 1230 do pola szerokość",
        intent="create_quote",
        capability_name="WH_WINDOW",
        capability_description="Controlled WindowHub execution.",
        skill_name="WHWindowSkill",
        scene=None,
    )

    parsed = _OpenAITaskReasoningProposal(
        actions=(
            _OpenAITaskReasoningAction(
                name="write_text",
                description="Enter the requested width.",
                target="Szerokość",
                value="1230",
            ),
        ),
        rationale="Populate the width field.",
        confidence=0.95,
        requires_manual_review=False,
    )

    client = FakeClient(parsed)
    reasoner = OpenAITaskReasoner(
        config=create_config(),
        client=client,
    )

    proposal = reasoner.reason(context)

    assert proposal is not None
    assert proposal.actions[0].name == "write_text"
    assert proposal.actions[0].target == "Szerokość"
    assert proposal.actions[0].value == "1230"



def test_openai_task_reasoner_receives_application_knowledge():
    context = TaskPlanningContext(
        request_message="Przygotuj nową ofertę",
        intent="create_quote",
        capability_name="WH_WINDOW",
        capability_description="Controlled WindowHub execution.",
        skill_name="WHWindowSkill",
        application_knowledge={
            "application": "WindowHub",
            "workflow": (
                {
                    "stage": 1,
                    "name": "start_new_offer",
                    "expected_visible_controls": ("Nowa oferta",),
                },
            ),
        },
    )

    parsed = _OpenAITaskReasoningProposal(
        actions=(
            _OpenAITaskReasoningAction(
                name="click_screen_element",
                description="Start the visible new offer workflow.",
                target="NOWA OFERTA",
            ),
        ),
        rationale="Use the WindowHub workflow knowledge and visible control.",
        confidence=0.96,
        requires_manual_review=False,
    )

    client = FakeClient(parsed)
    reasoner = OpenAITaskReasoner(
        config=create_config(),
        client=client,
    )

    proposal = reasoner.reason(context)

    assert proposal is not None
    payload = json.loads(
        client.responses.calls[0]["input"]
    )
    assert payload["application_knowledge"]["application"] == "WindowHub"


def test_openai_task_reasoner_includes_current_screenshot_when_available():
    scene = ScreenScene(
        observation=EnvironmentObservation(
            state=EnvironmentState(
                active_application="WindowHub",
                active_window_title="Okna - WindowHub",
            ),
            metadata={
                "screenshot": Screenshot(
                    width=2,
                    height=2,
                    image=np.zeros(
                        (2, 2, 4),
                        dtype=np.uint8,
                    ),
                ),
            },
        ),
        elements=(),
    )

    context = TaskPlanningContext(
        request_message="Przygotuj ofertę.",
        intent="create_quote",
        capability_name="WH_WINDOW",
        capability_description="Controlled WindowHub execution.",
        skill_name="WHWindowSkill",
        scene=scene,
    )

    parsed = _OpenAITaskReasoningProposal(
        actions=(
            _OpenAITaskReasoningAction(
                name="click_screen_element",
                description="Continue the visible workflow.",
                target="OK",
            ),
        ),
        rationale="Use the observed GUI state.",
        confidence=0.9,
        requires_manual_review=False,
    )

    client = FakeClient(parsed)
    reasoner = OpenAITaskReasoner(
        config=create_config(),
        client=client,
    )

    proposal = reasoner.reason(context)

    assert proposal is not None

    model_input = client.responses.calls[0]["input"]
    assert isinstance(model_input, list)
    assert model_input[0]["content"][0]["type"] == "input_text"
    assert model_input[0]["content"][1]["type"] == "input_image"
    assert model_input[0]["content"][1]["image_url"].startswith(
        "data:image/png;base64,"
    )
