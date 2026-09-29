from app.agent.perception.interaction_capability import (
    InteractionCapability,
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


def evidence(
    *,
    source,
    value,
    kind=EvidenceKind.CONTROL_TYPE,
    confidence=0.8,
    element_id=None,
):
    return SemanticEvidence(
        source=source,
        kind=kind,
        value=value,
        confidence=confidence,
        element_id=element_id or f"{source.value}-1",
    )


def element(
    *,
    source,
    kind="unknown",
    label=None,
    confidence=0.8,
    metadata=None,
    evidence_items=(),
):
    base_metadata = {"source": source}
    if metadata:
        base_metadata.update(metadata)

    return ScreenElement(
        kind=kind,
        label=label,
        x=10,
        y=20,
        width=80,
        height=30,
        confidence=confidence,
        metadata=base_metadata,
        evidence=tuple(evidence_items),
    )


def test_same_source_tracked_object_is_fused():
    items = (
        element(
            source="vision",
            kind="button",
            metadata={"tracked_object_id": "TO-1"},
            evidence_items=(
                evidence(
                    source=EvidenceSource.VISUAL,
                    value="button",
                    element_id="TO-1",
                ),
            ),
        ),
        element(
            source="vision",
            kind="button",
            label="Save",
            confidence=0.95,
            metadata={"tracked_object_id": "TO-1"},
            evidence_items=(
                evidence(
                    source=EvidenceSource.TEMPORAL,
                    kind=EvidenceKind.STABILITY,
                    value=2,
                    confidence=1.0,
                    element_id="TO-1",
                ),
            ),
        ),
    )

    result = ScreenElementFusion().fuse(items)

    assert len(result.elements) == 1
    assert result.merged_group_count == 1
    assert result.elements[0].label == "Save"
    assert result.elements[0].metadata["fused"] is True


def test_cross_provider_semantic_name_is_fused_and_capability_is_aggregated():
    items = (
        element(
            source="vision",
            kind="icon",
            confidence=0.75,
            metadata={"semantic_name": "save"},
            evidence_items=(
                evidence(
                    source=EvidenceSource.VISUAL,
                    value="button",
                    confidence=0.75,
                ),
            ),
        ),
        element(
            source="accessibility",
            kind="button",
            label="Save",
            confidence=0.99,
            metadata={"semantic_name": "save"},
            evidence_items=(
                evidence(
                    source=EvidenceSource.ACCESSIBILITY,
                    kind=EvidenceKind.INTERACTION_CAPABILITY,
                    value="clickable",
                    confidence=0.99,
                ),
            ),
        ),
    )

    result = ScreenElementFusion().fuse(items)

    assert len(result.elements) == 1
    fused = result.elements[0]

    assert result.merged_group_count == 1
    assert fused.interaction_capability is InteractionCapability.CLICKABLE
    assert fused.metadata["fused_provider_count"] == 2
    assert set(fused.metadata["fusion_sources"]) == {
        "accessibility",
        "vision",
    }
    assert len(fused.evidence) == 2


def test_duplicate_semantic_name_in_one_provider_blocks_cross_provider_merge():
    items = (
        element(
            source="vision",
            kind="button",
            metadata={"semantic_name": "save"},
        ),
        element(
            source="vision",
            kind="button",
            metadata={"semantic_name": "save"},
        ),
        element(
            source="accessibility",
            kind="button",
            metadata={"semantic_name": "save"},
        ),
    )

    result = ScreenElementFusion().fuse(items)

    assert len(result.elements) == 3
    assert result.merged_group_count == 0


def test_same_geometry_without_identity_is_not_fused():
    items = (
        element(source="vision", kind="icon"),
        element(source="accessibility", kind="button"),
    )

    result = ScreenElementFusion().fuse(items)

    assert len(result.elements) == 2
    assert result.merged_group_count == 0


def test_same_label_across_unique_providers_is_fused():
    items = (
        element(
            source="vision",
            kind="button",
            label="Save",
        ),
        element(
            source="accessibility",
            kind="button",
            label="Save",
        ),
    )

    result = ScreenElementFusion().fuse(items)

    assert len(result.elements) == 1
    assert result.merged_group_count == 1


def test_conflicting_explicit_capabilities_remain_unknown_after_fusion():
    items = (
        element(
            source="accessibility",
            kind="button",
            metadata={"semantic_name": "save"},
            evidence_items=(
                evidence(
                    source=EvidenceSource.ACCESSIBILITY,
                    kind=EvidenceKind.INTERACTION_CAPABILITY,
                    value="clickable",
                    confidence=0.99,
                ),
            ),
        ),
        element(
            source="ocr",
            kind="text",
            metadata={"semantic_name": "save"},
            evidence_items=(
                evidence(
                    source=EvidenceSource.OCR,
                    kind=EvidenceKind.INTERACTION_CAPABILITY,
                    value="not_interactive",
                    confidence=0.90,
                ),
            ),
        ),
    )

    result = ScreenElementFusion().fuse(items)

    assert len(result.elements) == 1
    assert (
        result.elements[0].interaction_capability
        is InteractionCapability.UNKNOWN
    )
