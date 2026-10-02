import pytest

from app.agent.reasoning.knowledge_context import (
    KnowledgeContext,
    KnowledgeConflict,
    KnowledgeFact,
    KnowledgeSource,
    KnowledgeSourceQuality,
    validate_knowledge_envelope,
)
from app.agent.reasoning.task_planning_context import TaskPlanningContext


def _source():
    return KnowledgeSource(
        source_id="source-1",
        title="Manufacturer documentation",
        url="https://example.com/spec",
        domain="example.com",
        retrieved_at="2026-10-02T09:15:00Z",
    )


def test_knowledge_context_serializes_provenance_and_confidence():
    context = KnowledgeContext(
        status="complete",
        query="Product X specification",
        sources=(_source(),),
        facts=(
            KnowledgeFact(
                fact_id="fact-1",
                claim="Product X supports triple glazing.",
                source_ids=("source-1",),
                confidence=0.94,
                relevance=0.91,
                evidence="Specification section 4.",
            ),
        ),
    )

    payload = context.to_payload()

    assert payload["version"] == "1"
    assert payload["status"] == "complete"
    assert payload["facts"][0]["confidence"] == 0.94
    assert payload["facts"][0]["source_ids"] == ["source-1"]
    assert payload["sources"][0]["url"] == "https://example.com/spec"


def test_knowledge_context_rejects_unknown_fact_source():
    context = KnowledgeContext(
        status="partial",
        sources=(_source(),),
        facts=(
            KnowledgeFact(
                fact_id="fact-1",
                claim="Unsupported reference.",
                source_ids=("missing-source",),
                confidence=0.5,
                relevance=0.5,
            ),
        ),
    )

    with pytest.raises(ValueError, match="unknown source"):
        context.validate()


def test_knowledge_context_rejects_conflict_with_unknown_fact():
    context = KnowledgeContext(
        status="conflict",
        sources=(_source(),),
        facts=(
            KnowledgeFact(
                fact_id="fact-1",
                claim="Value A.",
                source_ids=("source-1",),
                confidence=0.6,
                relevance=0.8,
            ),
        ),
        conflicts=(
            KnowledgeConflict(
                conflict_id="conflict-1",
                topic="value",
                fact_ids=("fact-1", "missing-fact"),
            ),
        ),
    )

    with pytest.raises(ValueError, match="unknown fact"):
        context.validate()


def test_knowledge_context_rejects_non_http_source():
    context = KnowledgeContext(
        sources=(
            KnowledgeSource(
                source_id="source-1",
                title="Local file",
                url="file:///secret.txt",
            ),
        )
    )

    with pytest.raises(ValueError, match="http or https"):
        context.validate()


def test_task_planning_context_keeps_external_knowledge_explicit():
    context = TaskPlanningContext(
        request_message="Sprawdź parametr produktu.",
        intent="computer_use",
        external_knowledge=KnowledgeContext(
            status="complete",
            query="parametr produktu",
            sources=(_source(),),
            facts=(
                KnowledgeFact(
                    fact_id="fact-1",
                    claim="Parameter value is 1.1.",
                    source_ids=("source-1",),
                    confidence=0.88,
                    relevance=0.95,
                ),
            ),
        ),
    )

    payload = context.to_payload()

    assert payload["external_knowledge"]["version"] == "1"
    assert payload["external_knowledge"]["facts"][0]["claim"] == (
        "Parameter value is 1.1."
    )


def test_knowledge_envelope_requires_version_and_separates_local_external():
    envelope = {
        "version": "1",
        "local": {"application": "WindowHub"},
        "external": KnowledgeContext.empty().to_payload(),
    }

    validate_knowledge_envelope(envelope)

    invalid = {
        "version": "2",
        "local": None,
        "external": None,
    }

    with pytest.raises(ValueError, match="version"):
        validate_knowledge_envelope(invalid)


def test_knowledge_context_round_trips_remote_payload():
    payload = KnowledgeContext(
        status="complete",
        query="parametr produktu",
        sources=(_source(),),
        facts=(
            KnowledgeFact(
                fact_id="fact-1",
                claim="Parameter value is 1.1.",
                source_ids=("source-1",),
                confidence=0.88,
                relevance=0.91,
                evidence="Manufacturer specification.",
                kind="assertion",
                provider_score=0.94,
            ),
        ),
        limitations=("Freshness depends on the publication date.",),
    ).to_payload()

    restored = KnowledgeContext.from_payload(payload)

    assert restored.status == "complete"
    assert restored.query == "parametr produktu"
    assert restored.sources[0].source_id == "source-1"
    assert restored.facts[0].provider_score == 0.94
    assert restored.to_payload() == payload

def test_knowledge_context_round_trips_source_quality_metadata():
    quality = KnowledgeSourceQuality(
        tier="authoritative",
        score=0.93,
        authority_score=1.0,
        temporal_fit_score=0.9,
        topical_fit_score=0.88,
        reasons=(
            "Official government source domain.",
            "Publication date matches the requested year.",
        ),
    )

    context = KnowledgeContext(
        status="complete",
        query="aktualne wymagania techniczne Niemcy 2024",
        sources=(
            KnowledgeSource(
                source_id="web-1",
                title="German official source",
                url="https://example.bund.de/rules",
                domain="example.bund.de",
                source_type="web_search_result",
                quality=quality,
            ),
        ),
    )

    payload = context.to_payload()
    restored = KnowledgeContext.from_payload(payload)

    assert restored.sources[0].quality is not None
    assert restored.sources[0].quality.tier == "authoritative"
    assert restored.sources[0].quality.score == 0.93
    assert restored.sources[0].quality.reasons == quality.reasons
    assert restored.to_payload() == payload
