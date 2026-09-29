import os

import pytest

from app.runtime.execution.interactions.interaction_action import (
    InteractionAction,
)
from app.runtime.execution.robot_action_executor import (
    RobotActionExecutor,
    RobotExecutionMode,
)
from app.runtime.execution.vision.pipeline.vision_pipeline import (
    VisionPipeline,
)


class ProbeSafetyGate:
    """
    Test-only gate.

    Allows stable ICON CLICK candidates so the integration test
    can exercise Bridge + center resolution without enabling
    production ICON execution policy.
    """

    def can_execute(
        self,
        tracked_object,
        action,
        **_,
    ):
        return (
            action is InteractionAction.CLICK
            and tracked_object.control_type is not None
            and str(tracked_object.control_type).endswith("ICON")
        )


@pytest.mark.integration
def test_real_windowhub_stable_icons_resolve_to_dry_run_clicks():
    if os.environ.get("WH_REAL_WINDOWHUB") != "1":
        pytest.skip(
            "Set WH_REAL_WINDOWHUB=1 to run against the real WindowHub"
        )

    pipeline = VisionPipeline()

    pipeline.observe()
    context = pipeline.observe()

    icons = [
        obj
        for obj in context.tracked_objects
        if (
            obj.control_type is not None
            and str(obj.control_type).endswith("ICON")
            and obj.status.value == "stable"
        )
    ]

    assert icons, "Expected at least one stable ICON in WindowHub"

    executor = RobotActionExecutor(
        mode=RobotExecutionMode.DRY_RUN,
        safety_gate=ProbeSafetyGate(),
    )

    results = []

    for target in icons:
        result = executor.execute(
            tracked_object=target,
            action=InteractionAction.CLICK,
            root=context.scene_graph.root,
        )

        results.append(result)

        assert result.success is True
        assert result.executed is False
        assert result.mode is RobotExecutionMode.DRY_RUN
        assert result.target_id is not None
        assert result.point is not None
        assert result.confidence > 0.0
        assert result.point[0] >= 0
        assert result.point[1] >= 0
        assert "hardware not touched" in result.reason

    assert len(results) == len(icons)
