from types import SimpleNamespace

from app.agent.agent_request import AgentRequest
from app.agent.learning.agent_mode import AgentMode
from app.agent.learning.learned_workflow import LearnedAction
from app.agent.learning.learning_recorder import LearningRecorder
from app.agent.learning.semantic_snapshot import SemanticSnapshot
from app.agent.learning.workflow_memory_store import WorkflowMemoryStore
from app.agent.perception.interaction_capability import InteractionCapability
from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.screen_scene import ScreenScene


def _scene(
    *,
    application="TestApp",
    label="Save",
    current_value="draft",
):
    observation = SimpleNamespace(
        state=SimpleNamespace(
            active_application=application,
            active_window_title="Test Window",
        )
    )
    element = ScreenElement(
        kind="button",
        label=label,
        confidence=0.95,
        interaction_capability=InteractionCapability.CLICKABLE,
        metadata={
            "current_value": current_value,
            "semantic_label": label,
            "x": 100,
            "automation_id": "internal-only",
        },
    )
    return ScreenScene(
        observation=observation,
        elements=(element,),
    )


def test_agent_request_has_explicit_operating_mode():
    request = AgentRequest(
        message="naucz się tego workflow",
        mode=AgentMode.LEARN,
    )

    assert request.mode is AgentMode.LEARN


def test_semantic_snapshot_excludes_physical_gui_identifiers():
    snapshot = SemanticSnapshot.from_scene(_scene())

    payload = snapshot.to_payload()

    assert payload["application"] == "TestApp"
    assert payload["elements"][0]["label"] == "Save"
    assert "x" not in payload["elements"][0]
    assert "automation_id" not in payload["elements"][0]


def test_learning_recorder_builds_semantic_workflow():
    recorder = LearningRecorder()

    recorder.start(
        workflow_id="wf-001",
        name="Save document",
        trigger="zapisz dokument",
        application="TestApp",
    )

    recorder.record_step(
        action=LearnedAction(
            name="click_screen_element",
            target="Save",
            description="Save the current document.",
        ),
        before=SemanticSnapshot.from_scene(_scene()),
        after=SemanticSnapshot.from_scene(
            _scene(label="Saved"),
        ),
    )

    workflow = recorder.finish(
        notes="First demonstrated office workflow.",
    )

    assert not recorder.is_recording
    assert workflow.workflow_id == "wf-001"
    assert len(workflow.steps) == 1
    assert workflow.steps[0].action.target == "Save"


def test_workflow_memory_finds_by_application_and_trigger():
    recorder = LearningRecorder()
    recorder.start(
        workflow_id="wf-002",
        name="Prepare report",
        trigger="przygotuj raport",
        application="Excel",
    )
    recorder.record_step(
        action=LearnedAction(
            name="select",
            target="Tabela",
        ),
        before=SemanticSnapshot.from_scene(
            _scene(application="Excel"),
        ),
    )
    workflow = recorder.finish()

    store = WorkflowMemoryStore()
    store.save(workflow)

    matches = store.find(
        application="excel",
        trigger="raport",
    )

    assert [item.workflow_id for item in matches] == ["wf-002"]
