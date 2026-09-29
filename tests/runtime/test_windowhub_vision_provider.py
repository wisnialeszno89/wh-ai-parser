from types import SimpleNamespace

from app.agent.environment.environment_observation import (
    EnvironmentObservation,
)
from app.agent.environment.environment_state import (
    EnvironmentState,
)
from app.agent.perception.windowhub_vision_provider import (
    WindowHubVisionProvider,
)


class EmptyVisionPipeline:
    def __init__(self):
        self.kwargs = None

    def observe(self, **kwargs):
        self.kwargs = kwargs
        return SimpleNamespace(
            tracked_objects=None,
            scene_graph=None,
        )


def test_windowhub_provider_handles_empty_tracked_objects():
    pipeline = EmptyVisionPipeline()

    observation = EnvironmentObservation(
        state=EnvironmentState(),
        metadata={
            "window_rect": "window",
            "screenshot": "screenshot",
        },
    )

    elements = WindowHubVisionProvider(
        vision_pipeline=pipeline,
    ).perceive(observation)

    assert elements == ()

    runtime = observation.metadata["execution_runtime"]

    assert runtime["robot_tracked_objects"] == ()
    assert runtime["gui_object_root"] is None
    assert pipeline.kwargs == {
        "window": "window",
        "screenshot": "screenshot",
    }
