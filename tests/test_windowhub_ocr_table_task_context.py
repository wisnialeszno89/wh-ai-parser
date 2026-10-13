import json

from app.agent.environment.environment_observation import EnvironmentObservation
from app.agent.environment.environment_state import EnvironmentState
from app.agent.perception.screen_scene import ScreenScene
from app.agent.perception.windowhub_ocr_table_parser import WindowHubOCRTableRow
from app.agent.perception.windowhub_ocr_table_pipeline import WindowHubOCRTableReconstruction
from app.agent.reasoning.task_planning_context import TaskPlanningContext
from app.agent.world.semantic_world_model import SemanticWorldModel


def make_scene():
    row = WindowHubOCRTableRow(
        row_index=1, lp=1, lp_source="ocr_column", quantity=1, article="Okno",
        net_total="1045.18", unit_value="1045.18", dimensions="1320 x 1345",
        center_y=223.9, missing_fields=(),
    )
    reconstruction = WindowHubOCRTableReconstruction((row,), (), ())
    observation = EnvironmentObservation(
        state=EnvironmentState(active_application="WindowHub", active_window_title="Okna - OFR/4170-"),
        metadata={"windowhub_ocr_table_reconstruction": reconstruction},
    )
    return ScreenScene(observation=observation, elements=(), metadata={
        "windowhub_ocr_table_reconstruction": reconstruction,
    })


def test_task_planning_scene_payload_contains_structured_table_rows():
    scene = make_scene()
    payload = TaskPlanningContext(request_message="Odczytaj ofertę", intent="computer_use", scene=scene).to_payload()
    table = payload["scene"]["structured_data"]["windowhub_ocr_table"]
    assert table["status"] == "complete"
    assert table["row_count"] == 1
    assert table["rows"][0]["lp"] == 1
    assert table["rows"][0]["net_total"] == "1045.18"
    assert "center_y" not in table["rows"][0]
    json.dumps(payload, ensure_ascii=False)


def test_semantic_world_payload_contains_table_as_data_not_affordance():
    world = SemanticWorldModel.from_scene(make_scene()).to_payload()
    assert world["metadata"]["windowhub_ocr_table"]["rows"][0]["article"] == "Okno"
    assert world["affordances"] == []


def test_payload_omits_table_when_reconstruction_cannot_be_serialized():
    scene = make_scene()
    scene.metadata["windowhub_ocr_table_reconstruction"] = object()
    payload = TaskPlanningContext(request_message="Odczytaj ofertę", intent="computer_use", scene=scene).to_payload()
    assert "structured_data" not in payload["scene"]

def test_replanning_payload_keeps_structured_table_data():
    from app.agent.perception.screen_scene_snapshot import ScreenSceneSnapshot
    from app.agent.reasoning.replanning_context import ReplanningContext

    scene = make_scene()
    context = ReplanningContext(
        request_message="Odczytaj ofertę",
        intent="computer_use",
        active_plan=(),
        failed_action_name="read_table",
        failed_action_description="Read the OFR table",
        attempt_number=1,
        execution_success=False,
        execution_message="Test failure",
        verification_verified=False,
        verification_reason="Outcome not verified",
        verification_confidence=0.0,
        scene=ScreenSceneSnapshot.from_scene(scene),
    )

    payload = context.to_payload()
    table = payload["scene"]["metadata"]["structured_data"]["windowhub_ocr_table"]
    assert table["rows"][0]["lp"] == 1
    assert table["rows"][0]["dimensions"] == "1320 x 1345"
    json.dumps(payload, ensure_ascii=False)

