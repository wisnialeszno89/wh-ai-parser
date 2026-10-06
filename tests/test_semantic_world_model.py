from types import SimpleNamespace

from app.agent.perception.interaction_capability import InteractionCapability
from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.screen_scene import ScreenScene
from app.agent.world.semantic_world_model import SemanticWorldModel


def _scene():
    observation = SimpleNamespace(
        state=SimpleNamespace(
            active_application="TestApp",
            active_window_title="Test Window",
        )
    )

    save_button = ScreenElement(
        kind="button",
        label="Zapisz",
        confidence=0.96,
        interaction_capability=InteractionCapability.CLICKABLE,
        metadata={
            "semantic_label": "Zapisz",
            "automation_id": "must-not-leak",
        },
    )

    name_field = ScreenElement(
        kind="edit",
        label="Nazwa klienta",
        confidence=0.92,
        interaction_capability=InteractionCapability.UNKNOWN,
        metadata={
            "current_value": "Kowalski",
            "role": "field",
            "document_scope": "OFR/123",
            "runtime_id": "must-not-leak",
        },
    )

    return ScreenScene(
        observation=observation,
        elements=(save_button, name_field),
        metadata={"active_document": "OFR/123"},
    )


def test_world_model_builds_semantic_entities_and_affordances():
    world = SemanticWorldModel.from_scene(_scene())

    assert world.application == "TestApp"
    assert world.active_document == "OFR/123"

    save = world.find_entities("zapisz")
    assert len(save) == 1
    assert "click_screen_element" in save[0].affordance_names

    field = world.find_entities("Nazwa klienta")
    assert len(field) == 1
    assert field[0].current_value == "Kowalski"
    assert "write_text" in field[0].affordance_names

    assert {
        affordance.action_name
        for affordance in world.affordances
    } == {"click_screen_element", "write_text"}


def test_world_payload_contains_no_physical_gui_identifiers():
    payload = SemanticWorldModel.from_scene(_scene()).to_payload()

    entity = payload["entities"][0]

    assert "automation_id" not in entity
    assert "runtime_id" not in entity
    assert "x" not in entity
    assert "y" not in entity

    for affordance in payload["affordances"]:
        assert "window_handle" not in affordance
        assert "coordinate" not in affordance


def test_world_model_is_snapshot_not_mutating_scene():
    scene = _scene()
    world = SemanticWorldModel.from_scene(scene)

    assert len(scene.elements) == 2
    assert len(world.entities) == 2
