from dataclasses import dataclass

from app.agent.environment.environment_observation import (
    EnvironmentObservation,
)
from app.agent.environment.environment_state import (
    EnvironmentState,
)
from app.agent.perception.robot_vision_perception_engine import (
    RobotVisionPerceptionEngine,
)
from app.runtime.execution.vision.models.logical_object import (
    LogicalObject,
)
from app.runtime.execution.vision.models.tracked_object import (
    TrackedObject,
    TrackedObjectStatus,
)
from app.runtime.execution.vision.models.control_type import (
    ControlType,
)
from app.runtime.execution.vision.pipeline.vision_pipeline import (
    VisionPipeline,
)


@dataclass
class FakeBounds:
    x: int
    y: int
    width: int
    height: int


@dataclass
class FakeLogicalObject:
    bounds: FakeBounds


class FakeVisionPipeline(VisionPipeline):
    def __init__(self, tracked_objects):
        self._tracked_objects = tracked_objects

    def observe(self):
        return type(
            "FakeVisionContext",
            (),
            {
                "tracked_objects": self._tracked_objects,
            },
        )()


def make_tracked_object(
    *,
    object_id: str,
    control_type,
    status=TrackedObjectStatus.STABLE,
):
    return TrackedObject(
        id=object_id,
        object=FakeLogicalObject(
            bounds=FakeBounds(
                x=100,
                y=200,
                width=30,
                height=20,
            )
        ),
        control_type=control_type,
        confidence=0.91,
        consecutive_observations=3,
        status=status,
        stability=0.95,
    )


def make_observation():
    return EnvironmentObservation(
        state=EnvironmentState(
            active_application="WindowHub",
            active_window_title="Okna - OFR/3935-",
            screen_width=1936,
            screen_height=1168,
        )
    )


def test_robot_vision_perception_maps_tracked_object():
    tracked = make_tracked_object(
        object_id="TO-0004",
        control_type=ControlType.ICON,
    )

    engine = RobotVisionPerceptionEngine(
        vision_pipeline=FakeVisionPipeline([tracked])
    )

    scene = engine.perceive(
        make_observation()
    )

    assert len(scene.elements) == 1

    element = scene.elements[0]

    assert element.kind == ControlType.ICON
    assert element.label == "TO-0004"
    assert element.x == 100
    assert element.y == 200
    assert element.width == 30
    assert element.height == 20
    assert element.confidence == 0.91

    assert element.metadata is not None
    assert element.metadata["tracked_object_id"] == "TO-0004"
    assert element.metadata["status"] == "stable"


def test_robot_vision_perception_filters_lost_objects():
    stable = make_tracked_object(
        object_id="TO-0001",
        control_type=ControlType.ICON,
    )

    lost = make_tracked_object(
        object_id="TO-0002",
        control_type=ControlType.ICON,
        status=TrackedObjectStatus.LOST,
    )

    engine = RobotVisionPerceptionEngine(
        vision_pipeline=FakeVisionPipeline(
            [stable, lost]
        )
    )

    scene = engine.perceive(
        make_observation()
    )

    assert len(scene.elements) == 1
    assert scene.elements[0].label == "TO-0001"


def test_robot_vision_perception_preserves_scene_metadata():
    tracked = make_tracked_object(
        object_id="TO-0004",
        control_type=ControlType.ICON,
    )

    engine = RobotVisionPerceptionEngine(
        vision_pipeline=FakeVisionPipeline([tracked])
    )

    scene = engine.perceive(
        make_observation()
    )

    assert scene.metadata["vision_source"] == "VisionPipeline"
    assert scene.metadata["tracked_object_count"] == 1
