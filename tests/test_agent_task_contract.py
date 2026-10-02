from types import SimpleNamespace

from app.agent.bridge.agent_action_result import AgentActionResult
from app.agent.bridge.agent_task_contract import AgentTaskContract
from app.agent.bridge.world_state import WorldState


def test_agent_task_contract_exposes_semantics_without_coordinates():
    scene = SimpleNamespace(
        observation=SimpleNamespace(
            state=SimpleNamespace(
                active_application="WindowHub",
                active_window_title="WindowHub",
            )
        ),
        elements=(
            SimpleNamespace(
                kind="button",
                label="Następna sekcja",
                interaction_capability=SimpleNamespace(value="clickable"),
                metadata={"current_value": ""},
                confidence=0.99,
            ),
        ),
    )

    world = WorldState.from_scene(scene)
    contract = AgentTaskContract(
        task_id="task-1",
        goal="Otwórz następną sekcję",
        intent="computer_use",
        world=world,
    )

    payload = contract.to_payload()

    assert payload["world"]["active_application"] == "WindowHub"
    assert payload["world"]["visible_elements"][0]["label"] == "Następna sekcja"
    assert "x" not in payload["world"]["visible_elements"][0]
    assert "y" not in payload["world"]["visible_elements"][0]


def test_agent_action_result_keeps_semantic_execution_boundary():
    result = AgentActionResult(
        action_id="action-1",
        name="click_screen_element",
        target="Następna sekcja",
        value=None,
        success=True,
        verified=True,
        reason="visible target confirmed",
    )

    payload = result.to_payload()

    assert payload["name"] == "click_screen_element"
    assert payload["target"] == "Następna sekcja"
    assert payload["verified"] is True
