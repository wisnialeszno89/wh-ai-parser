from app.agent.agent_action import AgentAction
from app.agent.agent_request import AgentRequest
from app.agent.environment.environment_observation import (
    EnvironmentObservation,
)
from app.agent.environment.environment_state import (
    EnvironmentState,
)
from app.agent.perception.screen_element import (
    ScreenElement,
)
from app.agent.perception.screen_scene import (
    ScreenScene,
)
from app.agent.reasoning.navimind_client import (
    NaviMindClient,
    NaviMindClientError,
)
from app.agent.reasoning.navimind_config import (
    NaviMindConfig,
)
from app.agent.reasoning.navimind_context_builder import (
    NaviMindContextBuilder,
)
from app.agent.reasoning.navimind_contract import (
    NaviMindActionResponse,
    NaviMindReasoningResponse,
    NaviMindTaskContract,
)


def make_scene() -> ScreenScene:
    observation = EnvironmentObservation(
        state=EnvironmentState(
            active_application="WindowHub",
            active_window_title="Offer - Test",
        )
    )

    return ScreenScene(
        observation=observation,
        elements=(
            ScreenElement(
                kind="button",
                label="Save",
                x=100,
                y=200,
                width=80,
                height=30,
                confidence=0.97,
                metadata={
                    "interaction_capability": "click",
                    "runtime_id": "SHOULD_NOT_ESCAPE",
                },
            ),
            ScreenElement(
                kind="text_field",
                label="Width",
                x=300,
                y=400,
                width=120,
                height=30,
                confidence=0.99,
                metadata={
                    "interaction_capability": "type",
                    "current_value": "1230",
                },
            ),
        ),
    )


def test_bridge_payload_is_semantic_only() -> None:
    scene = make_scene()

    request = AgentRequest(
        message="Przygotuj ofertę",
        session_id="session-1",
        salesman_id="salesman-1",
    )

    contract = NaviMindContextBuilder().build(
        request,
        scene.observation,
        scene,
    )

    payload = contract.to_payload()

    assert payload["world"]["element_count"] == 2

    first = payload["world"]["visible_elements"][0]

    assert first == {
        "kind": "button",
        "label": "Save",
        "interaction_capability": "click",
        "confidence": 0.97,
    }

    second = payload["world"]["visible_elements"][1]

    assert second == {
        "kind": "text_field",
        "label": "Width",
        "interaction_capability": "type",
        "current_value": "1230",
        "confidence": 0.99,
    }

    serialized = str(payload)

    assert "runtime_id" not in serialized
    assert "SHOULD_NOT_ESCAPE" not in serialized
    assert '"x":' not in serialized
    assert '"y":' not in serialized


def test_response_to_agent_action_preserves_semantic_fields() -> None:
    response = NaviMindReasoningResponse(
        version="1",
        task_id="task-1",
        status="continue",
        rationale="Fill width",
        confidence=0.94,
        action=NaviMindActionResponse(
            name="type",
            description="Enter the requested width",
            target="Width",
            value="1230",
        ),
        requires_manual_review=False,
    )

    action = NaviMindContextBuilder().to_agent_action(
        response
    )

    assert isinstance(action, AgentAction)
    assert action.name == "type"
    assert action.target == "Width"
    assert action.value == "1230"


def test_client_rejects_missing_continue_action() -> None:
    client = NaviMindClient(
        NaviMindConfig(
            url="http://127.0.0.1:9",
            timeout_seconds=0.1,
        )
    )

    try:
        client._parse_response(
            {
                "version": "1",
                "task_id": "task-1",
                "status": "continue",
                "rationale": "x",
                "confidence": 0.5,
                "action": None,
                "requires_manual_review": False,
            }
        )
    except NaviMindClientError:
        pass
    else:
        raise AssertionError(
            "Expected NaviMindClientError"
        )
