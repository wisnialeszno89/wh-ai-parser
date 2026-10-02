from app.agent.environment.environment_observation import (
    EnvironmentObservation,
)
from app.agent.environment.environment_state import (
    EnvironmentState,
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


class StaticProvider(PerceptionProvider):
    def __init__(self, elements):
        self.elements = tuple(elements)

    def perceive(self, observation):
        return self.elements


def make_element(
    *,
    source,
    semantic_name,
    kind,
    evidence_source,
    evidence_kind,
    evidence_value,
    confidence,
):
    return ScreenElement(
        kind=kind,
        confidence=confidence,
        metadata={
            "source": source,
            "semantic_name": semantic_name,
        },
        evidence=(
            SemanticEvidence(
                source=evidence_source,
                kind=evidence_kind,
                value=evidence_value,
                confidence=confidence,
                element_id=f"{source}-1",
            ),
        ),
    )


def test_perception_engine_fuses_provider_outputs():
    observation = EnvironmentObservation(
        state=EnvironmentState(),
        metadata={},
    )

    vision = StaticProvider(
        (
            make_element(
                source="vision",
                semantic_name="save",
                kind="icon",
                evidence_source=EvidenceSource.VISUAL,
                evidence_kind=EvidenceKind.CONTROL_TYPE,
                evidence_value="button",
                confidence=0.75,
            ),
        )
    )

    accessibility = StaticProvider(
        (
            make_element(
                source="accessibility",
                semantic_name="save",
                kind="button",
                evidence_source=EvidenceSource.ACCESSIBILITY,
                evidence_kind=EvidenceKind.INTERACTION_CAPABILITY,
                evidence_value="clickable",
                confidence=0.99,
            ),
        )
    )

    scene = PerceptionEngine(
        providers=(vision, accessibility),
    ).perceive(observation)

    assert len(scene.elements) == 1
    assert scene.metadata["provider_count"] == 2
    assert scene.metadata["raw_element_count"] == 2
    assert scene.metadata["element_count"] == 1
    assert scene.metadata["merged_group_count"] == 1

    element = scene.elements[0]

    assert element.interaction_capability.value == "clickable"
    assert element.metadata["fused"] is True
    assert element.metadata["fused_provider_count"] == 2


def test_perception_engine_keeps_ambiguous_elements_separate():
    observation = EnvironmentObservation(
        state=EnvironmentState(),
        metadata={},
    )

    scene = PerceptionEngine(
        providers=(
            StaticProvider(
                (
                    ScreenElement(
                        kind="button",
                        metadata={
                            "source": "vision",
                            "semantic_name": "save",
                        },
                    ),
                    ScreenElement(
                        kind="button",
                        metadata={
                            "source": "vision",
                            "semantic_name": "save",
                        },
                    ),
                )
            ),
            StaticProvider(
                (
                    ScreenElement(
                        kind="button",
                        metadata={
                            "source": "accessibility",
                            "semantic_name": "save",
                        },
                    ),
                )
            ),
        ),
    ).perceive(observation)

    assert len(scene.elements) == 3
    assert scene.metadata["merged_group_count"] == 0
