from app.agent.perception.interaction_capability import (
    InteractionCapability,
)
from app.agent.perception.interaction_capability_resolver import (
    InteractionCapabilityResolver,
)
from app.agent.perception.semantic_evidence import (
    EvidenceKind,
    EvidenceSource,
    SemanticEvidence,
)


def evidence(
    *,
    source=EvidenceSource.VISUAL,
    kind=EvidenceKind.CONTROL_TYPE,
    value="icon",
    confidence=0.7,
    element_id="TO-0004",
    observed=True,
):
    return SemanticEvidence(
        source=source,
        kind=kind,
        value=value,
        confidence=confidence,
        element_id=element_id,
        observed=observed,
    )


def test_button_control_type_infers_clickable():
    result = InteractionCapabilityResolver().resolve(
        (evidence(value="button", confidence=0.75),),
    )

    assert result.capability is InteractionCapability.CLICKABLE
    assert result.confidence == 0.75
    assert result.candidate is not None
    assert result.candidate.semantic_name == "clickable"
    assert result.candidate.inferred is True


def test_icon_control_type_stays_unknown():
    result = InteractionCapabilityResolver().resolve(
        (evidence(value="icon", confidence=0.676),),
    )

    assert result.capability is InteractionCapability.UNKNOWN
    assert result.candidate is None


def test_explicit_observed_capability_is_preserved():
    result = InteractionCapabilityResolver().resolve(
        (
            evidence(
                source=EvidenceSource.ACCESSIBILITY,
                kind=EvidenceKind.INTERACTION_CAPABILITY,
                value="clickable",
                confidence=0.99,
            ),
        ),
    )

    assert result.capability is InteractionCapability.CLICKABLE
    assert result.confidence == 0.99
    assert result.candidate is not None
    assert result.candidate.reason == "Observed interaction capability evidence."


def test_conflicting_explicit_capabilities_are_rejected():
    result = InteractionCapabilityResolver().resolve(
        (
            evidence(
                kind=EvidenceKind.INTERACTION_CAPABILITY,
                value="clickable",
                confidence=0.95,
            ),
            evidence(
                kind=EvidenceKind.INTERACTION_CAPABILITY,
                value="not_interactive",
                confidence=0.95,
            ),
        ),
    )

    assert result.capability is InteractionCapability.UNKNOWN
    assert result.confidence == 0.0
    assert result.candidate is None



def test_unknown_explicit_capability_does_not_block_button_inference():
    result = InteractionCapabilityResolver().resolve(
        (
            evidence(
                kind=EvidenceKind.INTERACTION_CAPABILITY,
                value="unknown",
                confidence=1.0,
            ),
            evidence(
                kind=EvidenceKind.CONTROL_TYPE,
                value="button",
                confidence=0.8,
            ),
        ),
    )

    assert result.capability is InteractionCapability.CLICKABLE
    assert result.confidence == 0.8


def test_observed_not_interactive_capability_overrides_visual_button_inference():
    result = InteractionCapabilityResolver().resolve(
        (
            evidence(
                source=EvidenceSource.ACCESSIBILITY,
                kind=EvidenceKind.INTERACTION_CAPABILITY,
                value="not_interactive",
                confidence=0.99,
            ),
            evidence(
                source=EvidenceSource.VISUAL,
                kind=EvidenceKind.CONTROL_TYPE,
                value="button",
                confidence=0.95,
            ),
        ),
    )

    assert result.capability is InteractionCapability.NOT_INTERACTIVE
    assert result.confidence == 0.99
