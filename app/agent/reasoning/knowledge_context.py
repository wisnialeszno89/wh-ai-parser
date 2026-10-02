"""Structured knowledge exchanged with the remote reasoning layer.

Knowledge is model input, not an execution command channel. External/web
knowledge is therefore explicit about provenance, confidence, relevance and
limitations before it can reach NaviMind.
"""

from __future__ import annotations

from dataclasses import dataclass

from urllib.parse import urlparse


KNOWLEDGE_CONTEXT_VERSION = "1"

MAX_FACTS = 32
MAX_SOURCES = 32
MAX_CONFLICTS = 16
MAX_LIMITATIONS = 16
MAX_CLAIM_LENGTH = 2000
MAX_EVIDENCE_LENGTH = 4000
MAX_TITLE_LENGTH = 500
MAX_URL_LENGTH = 2000
MAX_DOMAIN_LENGTH = 255
MAX_ID_LENGTH = 128
MAX_QUERY_LENGTH = 1000
MAX_DATE_LENGTH = 64


def _require_nonempty(value: str, field_name: str, max_length: int) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string.")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must not be empty.")
    if len(normalized) > max_length:
        raise ValueError(f"{field_name} exceeds the maximum length.")
    return normalized


def _validate_score(value: float, field_name: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{field_name} must be numeric.")
    normalized = float(value)
    if not 0.0 <= normalized <= 1.0:
        raise ValueError(f"{field_name} must be between 0 and 1.")
    return normalized


def _validate_optional_date(value: str | None, field_name: str) -> str | None:
    if value is None:
        return None
    return _require_nonempty(value, field_name, MAX_DATE_LENGTH)


def _validate_id_list(
    values: tuple[str, ...],
    field_name: str,
    max_items: int,
) -> tuple[str, ...]:
    if len(values) > max_items:
        raise ValueError(f"{field_name} contains too many items.")
    return tuple(
        _require_nonempty(value, field_name, MAX_ID_LENGTH)
        for value in values
    )


@dataclass(frozen=True)
class KnowledgeSourceQuality:
    tier: str
    score: float
    authority_score: float
    temporal_fit_score: float
    topical_fit_score: float
    reasons: tuple[str, ...] = ()

    def validate(self) -> None:
        if self.tier not in {
            "authoritative",
            "institutional",
            "established",
            "general",
            "low_confidence",
        }:
            raise ValueError("Unsupported knowledge source quality tier.")
        _validate_score(self.score, "source.quality.score")
        _validate_score(
            self.authority_score,
            "source.quality.authority_score",
        )
        _validate_score(
            self.temporal_fit_score,
            "source.quality.temporal_fit_score",
        )
        _validate_score(
            self.topical_fit_score,
            "source.quality.topical_fit_score",
        )
        if len(self.reasons) > 8:
            raise ValueError("Source quality contains too many reasons.")
        for reason in self.reasons:
            _require_nonempty(
                reason,
                "source.quality.reason",
                500,
            )

    def to_payload(self) -> dict[str, object]:
        self.validate()
        return {
            "tier": self.tier,
            "score": float(self.score),
            "authority_score": float(self.authority_score),
            "temporal_fit_score": float(self.temporal_fit_score),
            "topical_fit_score": float(self.topical_fit_score),
            "reasons": [reason.strip() for reason in self.reasons],
        }


@dataclass(frozen=True)
class KnowledgeSource:
    source_id: str
    title: str
    url: str
    domain: str | None = None
    source_type: str = "web"
    retrieved_at: str | None = None
    published_at: str | None = None
    quality: KnowledgeSourceQuality | None = None

    def validate(self) -> None:
        _require_nonempty(self.source_id, "source_id", MAX_ID_LENGTH)
        _require_nonempty(self.title, "source.title", MAX_TITLE_LENGTH)
        url = _require_nonempty(self.url, "source.url", MAX_URL_LENGTH)

        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError(
                "source.url must use http or https and include a host."
            )

        if self.domain is not None:
            _require_nonempty(self.domain, "source.domain", MAX_DOMAIN_LENGTH)

        _require_nonempty(
            self.source_type,
            "source.source_type",
            64,
        )
        _validate_optional_date(self.retrieved_at, "source.retrieved_at")
        _validate_optional_date(self.published_at, "source.published_at")
        if self.quality is not None:
            self.quality.validate()

    def to_payload(self) -> dict[str, object]:
        self.validate()
        payload: dict[str, object] = {
            "source_id": self.source_id.strip(),
            "title": self.title.strip(),
            "url": self.url.strip(),
            "source_type": self.source_type.strip(),
        }
        if self.domain is not None:
            payload["domain"] = self.domain.strip()
        if self.retrieved_at is not None:
            payload["retrieved_at"] = self.retrieved_at.strip()
        if self.published_at is not None:
            payload["published_at"] = self.published_at.strip()
        if self.quality is not None:
            payload["quality"] = self.quality.to_payload()
        return payload


@dataclass(frozen=True)
class KnowledgeFact:
    fact_id: str
    claim: str
    source_ids: tuple[str, ...] = ()
    confidence: float = 0.0
    relevance: float = 0.0
    evidence: str | None = None
    kind: str = "assertion"
    provider_score: float | None = None

    def validate(self) -> None:
        _require_nonempty(self.fact_id, "fact_id", MAX_ID_LENGTH)
        _require_nonempty(self.claim, "fact.claim", MAX_CLAIM_LENGTH)
        _validate_id_list(self.source_ids, "fact.source_ids", MAX_SOURCES)
        _validate_score(self.confidence, "fact.confidence")
        _validate_score(self.relevance, "fact.relevance")
        if self.kind not in {"assertion", "retrieved_evidence"}:
            raise ValueError("Unsupported knowledge fact kind.")
        if self.provider_score is not None:
            _validate_score(
                self.provider_score,
                "fact.provider_score",
            )
        if self.evidence is not None:
            _require_nonempty(
                self.evidence,
                "fact.evidence",
                MAX_EVIDENCE_LENGTH,
            )

    def to_payload(self) -> dict[str, object]:
        self.validate()
        payload: dict[str, object] = {
            "fact_id": self.fact_id.strip(),
            "claim": self.claim.strip(),
            "source_ids": list(self.source_ids),
            "confidence": float(self.confidence),
            "relevance": float(self.relevance),
            "kind": self.kind,
        }
        if self.provider_score is not None:
            payload["provider_score"] = float(self.provider_score)
        if self.evidence is not None:
            payload["evidence"] = self.evidence.strip()
        return payload


@dataclass(frozen=True)
class KnowledgeConflict:
    conflict_id: str
    topic: str
    fact_ids: tuple[str, ...] = ()
    description: str = ""

    def validate(self) -> None:
        _require_nonempty(
            self.conflict_id,
            "conflict_id",
            MAX_ID_LENGTH,
        )
        _require_nonempty(
            self.topic,
            "conflict.topic",
            MAX_CLAIM_LENGTH,
        )
        _validate_id_list(
            self.fact_ids,
            "conflict.fact_ids",
            MAX_FACTS,
        )
        if self.description:
            _require_nonempty(
                self.description,
                "conflict.description",
                MAX_CLAIM_LENGTH,
            )

    def to_payload(self) -> dict[str, object]:
        self.validate()
        payload: dict[str, object] = {
            "conflict_id": self.conflict_id.strip(),
            "topic": self.topic.strip(),
            "fact_ids": list(self.fact_ids),
        }
        if self.description:
            payload["description"] = self.description.strip()
        return payload


@dataclass(frozen=True)
class KnowledgeContext:
    """Validated external knowledge available to NaviMind."""

    status: str = "empty"
    query: str | None = None
    facts: tuple[KnowledgeFact, ...] = ()
    sources: tuple[KnowledgeSource, ...] = ()
    conflicts: tuple[KnowledgeConflict, ...] = ()
    limitations: tuple[str, ...] = ()
    version: str = KNOWLEDGE_CONTEXT_VERSION

    def validate(self) -> None:
        if self.version != KNOWLEDGE_CONTEXT_VERSION:
            raise ValueError("Unsupported knowledge context version.")

        allowed_statuses = {
            "empty",
            "partial",
            "complete",
            "conflict",
            "error",
        }
        if self.status not in allowed_statuses:
            raise ValueError("Unsupported knowledge context status.")

        if self.query is not None:
            _require_nonempty(self.query, "query", MAX_QUERY_LENGTH)

        if len(self.facts) > MAX_FACTS:
            raise ValueError("Knowledge context contains too many facts.")
        if len(self.sources) > MAX_SOURCES:
            raise ValueError("Knowledge context contains too many sources.")
        if len(self.conflicts) > MAX_CONFLICTS:
            raise ValueError("Knowledge context contains too many conflicts.")
        if len(self.limitations) > MAX_LIMITATIONS:
            raise ValueError(
                "Knowledge context contains too many limitations."
            )

        source_ids: set[str] = set()
        for source in self.sources:
            source.validate()
            source_id = source.source_id.strip()
            if source_id in source_ids:
                raise ValueError("Knowledge source ids must be unique.")
            source_ids.add(source_id)

        fact_ids: set[str] = set()
        for fact in self.facts:
            fact.validate()
            fact_id = fact.fact_id.strip()
            if fact_id in fact_ids:
                raise ValueError("Knowledge fact ids must be unique.")
            fact_ids.add(fact_id)

            unknown_sources = set(fact.source_ids) - source_ids
            if unknown_sources:
                raise ValueError(
                    "Knowledge fact references unknown source ids."
                )

        conflict_ids: set[str] = set()
        for conflict in self.conflicts:
            conflict.validate()
            conflict_id = conflict.conflict_id.strip()
            if conflict_id in conflict_ids:
                raise ValueError("Knowledge conflict ids must be unique.")
            conflict_ids.add(conflict_id)

            unknown_facts = set(conflict.fact_ids) - fact_ids
            if unknown_facts:
                raise ValueError(
                    "Knowledge conflict references unknown fact ids."
                )

        for limitation in self.limitations:
            _require_nonempty(
                limitation,
                "limitation",
                MAX_CLAIM_LENGTH,
            )

    def to_payload(self) -> dict[str, object]:
        self.validate()
        return {
            "version": self.version,
            "status": self.status,
            "query": (
                self.query.strip()
                if self.query is not None
                else None
            ),
            "facts": [
                fact.to_payload()
                for fact in self.facts
            ],
            "sources": [
                source.to_payload()
                for source in self.sources
            ],
            "conflicts": [
                conflict.to_payload()
                for conflict in self.conflicts
            ],
            "limitations": [
                limitation.strip()
                for limitation in self.limitations
            ],
        }

    @classmethod
    def from_payload(
        cls,
        payload: object,
    ) -> "KnowledgeContext":
        if not isinstance(payload, dict):
            raise ValueError("knowledge payload must be a mapping.")

        if payload.get("version") != KNOWLEDGE_CONTEXT_VERSION:
            raise ValueError("Unsupported knowledge context version.")

        status = payload.get("status")
        if not isinstance(status, str):
            raise ValueError("Knowledge context status must be a string.")

        query = payload.get("query")
        if query is not None and not isinstance(query, str):
            raise ValueError("Knowledge context query must be a string or null.")

        raw_sources = payload.get("sources")
        raw_facts = payload.get("facts")
        raw_conflicts = payload.get("conflicts")
        raw_limitations = payload.get("limitations")

        if not isinstance(raw_sources, list):
            raise ValueError("Knowledge context sources must be a list.")
        if not isinstance(raw_facts, list):
            raise ValueError("Knowledge context facts must be a list.")
        if not isinstance(raw_conflicts, list):
            raise ValueError("Knowledge context conflicts must be a list.")
        if not isinstance(raw_limitations, list):
            raise ValueError("Knowledge context limitations must be a list.")

        sources = []
        for item in raw_sources:
            if not isinstance(item, dict):
                raise ValueError("Knowledge source must be a mapping.")

            sources.append(
                KnowledgeSource(
                    source_id=str(item.get("source_id", "")),
                    title=str(item.get("title", "")),
                    url=str(item.get("url", "")),
                    domain=(
                        item.get("domain")
                        if isinstance(item.get("domain"), str)
                        else None
                    ),
                    source_type=str(
                        item.get("source_type", "web")
                    ),
                    retrieved_at=(
                        item.get("retrieved_at")
                        if isinstance(item.get("retrieved_at"), str)
                        else None
                    ),
                    published_at=(
                        item.get("published_at")
                        if isinstance(item.get("published_at"), str)
                        else None
                    ),
                    quality=(
                        KnowledgeSourceQuality(
                            tier=str(
                                item["quality"].get("tier", "")
                            ),
                            score=float(
                                item["quality"].get("score", 0.0)
                            ),
                            authority_score=float(
                                item["quality"].get(
                                    "authority_score",
                                    0.0,
                                )
                            ),
                            temporal_fit_score=float(
                                item["quality"].get(
                                    "temporal_fit_score",
                                    0.0,
                                )
                            ),
                            topical_fit_score=float(
                                item["quality"].get(
                                    "topical_fit_score",
                                    0.0,
                                )
                            ),
                            reasons=tuple(
                                value
                                for value in item["quality"].get(
                                    "reasons",
                                    [],
                                )
                                if isinstance(value, str)
                            ),
                        )
                        if isinstance(item.get("quality"), dict)
                        else None
                    ),
                )
            )

        facts = []
        for item in raw_facts:
            if not isinstance(item, dict):
                raise ValueError("Knowledge fact must be a mapping.")

            raw_source_ids = item.get("source_ids")
            if not isinstance(raw_source_ids, list):
                raise ValueError("Knowledge fact source_ids must be a list.")

            facts.append(
                KnowledgeFact(
                    fact_id=str(item.get("fact_id", "")),
                    claim=str(item.get("claim", "")),
                    source_ids=tuple(
                        value
                        for value in raw_source_ids
                        if isinstance(value, str)
                    ),
                    confidence=float(item.get("confidence", 0.0)),
                    relevance=float(item.get("relevance", 0.0)),
                    evidence=(
                        item.get("evidence")
                        if isinstance(item.get("evidence"), str)
                        else None
                    ),
                    kind=str(
                        item.get("kind", "assertion")
                    ),
                    provider_score=(
                        float(item["provider_score"])
                        if item.get("provider_score") is not None
                        else None
                    ),
                )
            )

        conflicts = []
        for item in raw_conflicts:
            if not isinstance(item, dict):
                raise ValueError("Knowledge conflict must be a mapping.")

            raw_fact_ids = item.get("fact_ids")
            if not isinstance(raw_fact_ids, list):
                raise ValueError("Knowledge conflict fact_ids must be a list.")

            conflicts.append(
                KnowledgeConflict(
                    conflict_id=str(item.get("conflict_id", "")),
                    topic=str(item.get("topic", "")),
                    fact_ids=tuple(
                        value
                        for value in raw_fact_ids
                        if isinstance(value, str)
                    ),
                    description=(
                        str(item.get("description", ""))
                        if item.get("description") is not None
                        else ""
                    ),
                )
            )

        limitations = tuple(
            value
            for value in raw_limitations
            if isinstance(value, str)
        )

        context = cls(
            status=status,
            query=query,
            facts=tuple(facts),
            sources=tuple(sources),
            conflicts=tuple(conflicts),
            limitations=limitations,
            version=KNOWLEDGE_CONTEXT_VERSION,
        )
        context.validate()
        return context

    @classmethod
    def empty(cls) -> "KnowledgeContext":
        return cls()


def validate_knowledge_envelope(value: dict[str, object]) -> None:
    """Validate the transport envelope used by AgentTaskContract."""
    if not isinstance(value, dict):
        raise ValueError("knowledge must be a mapping.")

    if value.get("version") != KNOWLEDGE_CONTEXT_VERSION:
        raise ValueError("Unsupported knowledge envelope version.")

    local = value.get("local")
    if local is not None and not isinstance(local, dict):
        raise ValueError("knowledge.local must be a mapping or null.")

    external = value.get("external")
    if external is not None:
        if not isinstance(external, dict):
            raise ValueError("knowledge.external must be a mapping or null.")
        if external.get("version") != KNOWLEDGE_CONTEXT_VERSION:
            raise ValueError(
                "Unsupported external knowledge context version."
            )
        status = external.get("status")
        if status not in {
            "empty",
            "partial",
            "complete",
            "conflict",
            "error",
        }:
            raise ValueError("Unsupported external knowledge status.")
