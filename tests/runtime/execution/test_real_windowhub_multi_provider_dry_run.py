import os
from dataclasses import replace

import pytest

from app.agent.environment.environment_state import EnvironmentState
from app.agent.environment.windowhub_environment_adapter import (
    WindowHubEnvironmentAdapter,
)
from app.agent.environment.environment_observation import (
    EnvironmentObservation,
)
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
from app.agent.perception.screen_element_fusion import (
    ScreenElementFusion,
)
from app.agent.perception.semantic_evidence import (
    EvidenceKind,
    EvidenceSource,
    SemanticEvidence,
)
from app.agent.perception.windowhub_vision_provider import (
    WindowHubVisionProvider,
)


class StaticProvider(PerceptionProvider):
    def __init__(self, elements):
        self.elements = tuple(elements)

    def perceive(self, observation: EnvironmentObservation):
        return self.elements


def make_accessibility_element(
    visual_element: ScreenElement,
    *,
    capability: str,
) -> ScreenElement:
    tracked_id = (
        visual_element.metadata or {}
    ).get("tracked_object_id")

    assert isinstance(tracked_id, str)

    shared_id = f"windowhub-test:{tracked_id}"

    return ScreenElement(
        kind="button",
        label="Synthetic Accessibility Target",
        x=visual_element.x,
        y=visual_element.y,
        width=visual_element.width,
        height=visual_element.height,
        confidence=0.99,
        interaction_capability=InteractionCapability(
            capability,
        ),
        metadata={
            "source": "synthetic_accessibility",
            "shared_id": shared_id,
            "provider_element_id": f"uia-test:{tracked_id}",
        },
        evidence=(
            SemanticEvidence(
                source=EvidenceSource.ACCESSIBILITY,
                kind=EvidenceKind.INTERACTION_CAPABILITY,
                value=capability,
                confidence=0.99,
                element_id=f"uia-test:{tracked_id}",
            ),
        ),
    )


@pytest.mark.integration
def test_real_windowhub_multi_provider_fusion_dry_run():
    if os.environ.get("WH_REAL_WINDOWHUB") != "1":
        pytest.skip(
            "Set WH_REAL_WINDOWHUB=1 to run against the real WindowHub"
        )

    environment = WindowHubEnvironmentAdapter()
    vision_provider = WindowHubVisionProvider()

    real_element = None

    for _ in range(3):
        observation = environment.observe()
        elements = vision_provider.perceive(observation)

        for element in elements:
            metadata = element.metadata or {}

            if (
                element.kind.casefold() == "icon"
                and metadata.get("status") == "stable"
                and metadata.get("consecutive_observations", 0) >= 2
            ):
                real_element = element

    if real_element is None:
        pytest.skip("No stable WindowHub ICON was available")

    tracked_id = (
        real_element.metadata or {}
    ).get("tracked_object_id")
    assert isinstance(tracked_id, str)

    shared_id = f"windowhub-test:{tracked_id}"

    correlated_visual = replace(
        real_element,
        metadata={
            **dict(real_element.metadata or {}),
            "shared_id": shared_id,
        },
    )

    accessibility = make_accessibility_element(
        real_element,
        capability="clickable",
    )

    engine = PerceptionEngine(
        providers=(
            StaticProvider((correlated_visual,)),
            StaticProvider((accessibility,)),
        )
    )

    scene = engine.perceive(
        EnvironmentState.__new__(EnvironmentObservation)
    )

    assert len(scene.elements) == 1
    assert scene.metadata["raw_element_count"] == 2
    assert scene.metadata["merged_group_count"] == 1

    fused = scene.elements[0]

    assert fused.interaction_capability is InteractionCapability.CLICKABLE
    assert fused.metadata["fused"] is True
    assert fused.metadata["fused_provider_count"] == 2
    assert set(fused.metadata["fusion_sources"]) == {
        "windowhub_vision_pipeline",
        "synthetic_accessibility",
    }
    assert len(fused.evidence) == 2

    conflicting = make_accessibility_element(
        real_element,
        capability="not_interactive",
    )
    conflicting = replace(
        conflicting,
        metadata={
            **dict(conflicting.metadata or {}),
            "source": "synthetic_ocr",
        },
        evidence=(
            replace(
                conflicting.evidence[0],
                source=EvidenceSource.OCR,
                element_id="ocr-test",
            ),
        ),
    )

    conflict_result = ScreenElementFusion().fuse(
        (
            correlated_visual,
            accessibility,
            conflicting,
        )
    )

    assert len(conflict_result.elements) == 1
    assert (
        conflict_result.elements[0].interaction_capability
        is InteractionCapability.UNKNOWN
    )
