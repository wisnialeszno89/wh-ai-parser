import pytest

from app.agent.perception.semantic_evidence import (
    EvidenceKind,
    EvidenceSource,
    SemanticCandidate,
    SemanticEvidence,
)


def test_observed_evidence_preserves_provenance():
    evidence = SemanticEvidence(
        source=EvidenceSource.VISUAL,
        kind=EvidenceKind.CONTROL_TYPE,
        value="icon",
        confidence=0.675,
        element_id="TO-0004",
    )

    assert evidence.source is EvidenceSource.VISUAL
    assert evidence.kind is EvidenceKind.CONTROL_TYPE
    assert evidence.value == "icon"
    assert evidence.confidence == 0.675
    assert evidence.element_id == "TO-0004"
    assert evidence.observed is True


def test_observed_evidence_requires_element_id():
    with pytest.raises(ValueError, match="identify the screen element"):
        SemanticEvidence(
            source=EvidenceSource.VISUAL,
            kind=EvidenceKind.CONTROL_TYPE,
            value="icon",
        )


def test_evidence_confidence_is_bounded():
    with pytest.raises(ValueError):
        SemanticEvidence(
            source=EvidenceSource.VISUAL,
            kind=EvidenceKind.CONTROL_TYPE,
            value="icon",
            confidence=1.1,
            element_id="TO-0004",
        )


def test_semantic_candidate_is_explicitly_an_inference():
    evidence = SemanticEvidence(
        source=EvidenceSource.VISUAL,
        kind=EvidenceKind.VISUAL_MATCH,
        value="settings_icon",
        confidence=0.72,
        element_id="TO-0004",
    )

    candidate = SemanticCandidate(
        semantic_name="settings",
        confidence=0.71,
        evidence=(evidence,),
        element_id="TO-0004",
        reason="Visual template match.",
    )

    assert candidate.semantic_name == "settings"
    assert candidate.confidence == 0.71
    assert candidate.element_id == "TO-0004"
    assert candidate.inferred is True
    assert candidate.evidence == (evidence,)


def test_semantic_candidate_confidence_is_bounded():
    with pytest.raises(ValueError):
        SemanticCandidate(
            semantic_name="settings",
            confidence=-0.1,
        )
