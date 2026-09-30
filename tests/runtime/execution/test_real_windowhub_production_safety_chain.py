import os
from dataclasses import replace

import pytest

from app.agent.agent_action import AgentAction
from app.agent.environment.environment_observation import (
    EnvironmentObservation,
)
from app.agent.environment.environment_state import (
    EnvironmentState,
)
from app.agent.environment.windowhub_environment_adapter import (
    WindowHubEnvironmentAdapter,
)
from app.agent.execution.execution_engine import ExecutionEngine
from app.agent.execution.executor_registry import ExecutorRegistry
from app.agent.execution.robot_gui_executor import RobotGUIExecutor
from app.agent.perception.interaction_capability import (
    InteractionCapability,
)
from app.agent.perception.perception_engine import (
    PerceptionEngine,
)
from app.agent.perception.perception_provider import (
    PerceptionProvider,
)
from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.semantic_evidence import (
    EvidenceKind,
    EvidenceSource,
    SemanticEvidence,
)
from app.agent.perception.windowhub_vision_provider import (
    WindowHubVisionProvider,
)
from app.agent.runtime.execution_context import (
    ExecutionContext,
)
from app.agent.agent_request import AgentRequest
from app.runtime.execution.robot_action_executor import (
    RobotActionExecutor,
    RobotExecutionMode,
)
from app.runtime.execution.robot_mouse import RobotMouse
from app.runtime.execution.vision.models.tracked_object import (
    TrackedObject,
)


class StaticAccessibilityProvider(PerceptionProvider):
    def __init__(self, element):
        self.element = element

    def perceive(self, observation: EnvironmentObservation):
        return (self.element,)


def make_accessibility_element(
    visual_element: ScreenElement,
) -> ScreenElement:
    tracked_id = (
        visual_element.metadata or {}
    ).get("tracked_object_id")

    assert isinstance(tracked_id, str)

    return ScreenElement(
        kind="button",
        label="Synthetic Accessibility Target",
        x=visual_element.x,
        y=visual_element.y,
        width=visual_element.width,
        height=visual_element.height,
        confidence=0.99,
        interaction_capability=InteractionCapability.CLICKABLE,
        metadata={
            "source": "synthetic_accessibility",
            "shared_id": f"windowhub-gate:{tracked_id}",
            "provider_element_id": (
                f"uia-gate:{tracked_id}"
            ),
        },
        evidence=(
            SemanticEvidence(
                source=EvidenceSource.ACCESSIBILITY,
                kind=EvidenceKind.INTERACTION_CAPABILITY,
                value="clickable",
                confidence=0.99,
                element_id=f"uia-gate:{tracked_id}",
            ),
        ),
    )


def build_executor():
    robot_gui_executor = RobotGUIExecutor(
        robot_action_executor=RobotActionExecutor(
            mode=RobotExecutionMode.DRY_RUN,
            mouse=RobotMouse(),
        ),
    )

    return ExecutionEngine(
        registry=ExecutorRegistry(
            executors=(robot_gui_executor,),
        ),
    )


@pytest.mark.integration
def test_real_windowhub_production_safety_gate_to_dry_run():
    if os.environ.get("WH_REAL_WINDOWHUB") != "1":
        pytest.skip(
            "Set WH_REAL_WINDOWHUB=1 to run against the real WindowHub"
        )

    environment = WindowHubEnvironmentAdapter()
    vision_provider = WindowHubVisionProvider()

    real_element = None
    runtime = None
    observation = None

    for _ in range(3):
        observation = environment.observe()
        elements = vision_provider.perceive(observation)

        runtime = observation.metadata["execution_runtime"]

        for element in elements:
            metadata = element.metadata or {}

            if (
                element.kind.casefold() == "icon"
                and metadata.get("status") == "stable"
                and metadata.get("consecutive_observations", 0) >= 2
            ):
                real_element = element
                break

        if real_element is not None:
            break

    if real_element is None:
        pytest.skip("No stable WindowHub ICON was available")

    tracked_objects = runtime["robot_tracked_objects"]
    gui_root = runtime["gui_object_root"]

    assert isinstance(tracked_objects, tuple)
    assert gui_root is not None

    tracked_id = (
        real_element.metadata or {}
    ).get("tracked_object_id")

    assert isinstance(tracked_id, str)

    request = AgentRequest(
        message="Kliknij potwierdzony semantic target.",
        session_id="real-windowhub-safety-chain",
        salesman_id="test",
    )

    context = ExecutionContext(
        request=request,
    )
    context.update_observation(observation)

    # Gate 1: raw WindowHub perception does not establish
    # clickability for an ICON.
    baseline_scene = PerceptionEngine(
        providers=(vision_provider,),
    ).perceive(observation)

    context.update_scene(baseline_scene)
    context.set_value(
        "robot_target_id",
        tracked_id,
    )
    context.set_value(
        "robot_tracked_objects",
        tracked_objects,
    )
    context.set_value(
        "gui_object_root",
        gui_root,
    )

    action = AgentAction(
        name="click_screen_element",
        description=f"Kliknij element {tracked_id}",
    )

    baseline_result = build_executor().execute(
        action=action,
        context=context,
    )

    assert baseline_result.success is False
    assert baseline_result.requires_manual_review is True
    assert baseline_result.metadata is not None
    assert (
        baseline_result.metadata["target_id"]
        == tracked_id
    )

    # Gate 2: add an independent accessibility capability
    # correlated to the same WindowHub target and let the
    # production fusion + SafetyGate evaluate it.
    accessible = make_accessibility_element(
        real_element,
    )

    # Use a production WindowHub provider together with the
    # synthetic capability provider so execution_runtime is
    # preserved by the real observation.
    real_scene = PerceptionEngine(
        providers=(
            vision_provider,
            StaticAccessibilityProvider(
                accessible,
            ),
        ),
    ).perceive(observation)

    assert real_scene.elements

    fused_element = next(
        element
        for element in real_scene.elements
        if (
            (element.metadata or {}).get(
                "tracked_object_id"
            )
            == tracked_id
        )
    )

    assert (
        fused_element.interaction_capability
        is InteractionCapability.CLICKABLE
    )

    context.update_scene(real_scene)

    fused_result = build_executor().execute(
        action=action,
        context=context,
    )

    assert fused_result.success is True
    assert fused_result.requires_manual_review is False
    assert fused_result.metadata is not None
    assert fused_result.metadata["target_id"] == tracked_id
    assert fused_result.metadata["executed"] is False
    assert fused_result.metadata["interaction_capability"] == "clickable"
    assert fused_result.metadata[
        "interaction_capability_confidence"
    ] > 0.0
    assert "hardware not touched" in fused_result.message
