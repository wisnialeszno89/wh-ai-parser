from enum import Enum

from app.agent.perception.interaction_capability import InteractionCapability
from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.screen_scene import ScreenScene
from app.agent.perception.screen_scene_snapshot import ScreenSceneSnapshot


class FakeControlType(str, Enum):
    ICON = "icon"


def test_snapshot_preserves_scene_evidence():
    element = ScreenElement(
        kind=FakeControlType.ICON,
        label="TO-0001",
        x=10,
        y=20,
        width=16,
        height=16,
        confidence=0.772,
        interaction_capability=InteractionCapability.UNKNOWN,
        metadata={
            "tracked_object_id": "TO-0001",
            "control_type": "icon",
            "status": "stable",
            "stability": 1.0,
            "consecutive_observations": 4,
        },
    )

    scene = ScreenScene(
        observation=None,
        elements=(element,),
        metadata={
            "vision_source": "VisionPipeline",
            "tracked_object_count": 1,
        },
    )

    snapshot = ScreenSceneSnapshot.from_scene(scene)

    assert len(snapshot.elements) == 1

    item = snapshot.elements[0]

    assert item.element_id == "TO-0001"
    assert item.kind == "icon"
    assert item.label == "TO-0001"
    assert item.x == 10
    assert item.y == 20
    assert item.width == 16
    assert item.height == 16
    assert item.confidence == 0.772
    assert item.interaction_capability == "unknown"

    assert item.metadata["tracked_object_id"] == "TO-0001"
    assert item.metadata["status"] == "stable"
    assert item.metadata["consecutive_observations"] == 4

    assert snapshot.metadata["vision_source"] == "VisionPipeline"


def test_snapshot_normalizes_control_type_enum():
    element = ScreenElement(
        kind=FakeControlType.ICON,
        label="TO-TEST",
    )

    scene = ScreenScene(
        observation=None,
        elements=(element,),
        metadata={},
    )

    snapshot = ScreenSceneSnapshot.from_scene(scene)

    assert snapshot.elements[0].kind == "icon"
