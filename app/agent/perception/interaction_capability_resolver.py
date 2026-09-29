from dataclasses import dataclass
from math import prod

from app.agent.perception.interaction_capability import (
    InteractionCapability,
)
from app.agent.perception.semantic_evidence import (
    EvidenceKind,
    EvidenceSource,
    SemanticCandidate,
    SemanticEvidence,
)


@dataclass(frozen=True)
class InteractionCapabilityResolution:
    """
    Result of inferring interaction capability from semantic evidence.

    Capability is an inference and must not be treated as execution
    authorization. Execution policy remains a separate concern.
    """

    capability: InteractionCapability
    confidence: float
    candidate: SemanticCandidate | None = None
    reason: str = ""
    supporting_sources: tuple[EvidenceSource, ...] = ()
    conflicting_capabilities: tuple[InteractionCapability, ...] = ()


@dataclass(frozen=True)
class _CapabilityClaim:
    capability: InteractionCapability
    evidence: SemanticEvidence
    observed_capability: bool


class InteractionCapabilityResolver:
    """
    Resolve interaction capability from the existing SemanticEvidence model.

    The resolver is deliberately conservative and source-aware:

    - observed INTERACTION_CAPABILITY evidence takes precedence over
      inferred control-type evidence
    - UNKNOWN capability values represent lack of knowledge and are ignored
    - BUTTON control-type evidence can infer CLICKABLE
    - multiple sources supporting the same capability are aggregated
    - repeated evidence from one source is reduced to its strongest claim
    - conflicting observed capabilities remain UNKNOWN
    - semantic inference never authorizes execution or bypasses SafetyGate

    Aggregation is a confidence combination over independent evidence
    sources. For a capability supported by source confidences c1..cn:

        combined = 1 - product(1 - ci)

    Evidence from the same source is not combined more than once.
    """

    MAX_AGGREGATED_CONFIDENCE = 0.999

    def resolve(
        self,
        evidence: tuple[SemanticEvidence, ...],
        *,
        element_id: str | None = None,
    ) -> InteractionCapabilityResolution:

        claims = self._claims_from_evidence(evidence)

        observed_claims = tuple(
            claim
            for claim in claims
            if claim.observed_capability
        )

        observed_capabilities = {
            claim.capability
            for claim in observed_claims
        }

        if len(observed_capabilities) > 1:
            conflicting = tuple(sorted(
                observed_capabilities,
                key=lambda capability: capability.value,
            ))
            return InteractionCapabilityResolution(
                capability=InteractionCapability.UNKNOWN,
                confidence=0.0,
                reason=(
                    "Conflicting observed interaction capability evidence."
                ),
                conflicting_capabilities=conflicting,
            )

        if len(observed_capabilities) == 1:
            capability = next(iter(observed_capabilities))
            supporting = tuple(
                claim
                for claim in claims
                if claim.capability is capability
            )
            return self._build_resolution(
                capability=capability,
                claims=supporting,
                element_id=element_id,
                reason=(
                    "Observed interaction capability evidence aggregated "
                    "across available sources."
                ),
            )

        inferred_claims = tuple(claim for claim in claims)
        inferred_capabilities = {
            claim.capability
            for claim in inferred_claims
        }

        if len(inferred_capabilities) > 1:
            conflicting = tuple(sorted(
                inferred_capabilities,
                key=lambda capability: capability.value,
            ))
            return InteractionCapabilityResolution(
                capability=InteractionCapability.UNKNOWN,
                confidence=0.0,
                reason=(
                    "Conflicting inferred interaction capabilities."
                ),
                conflicting_capabilities=conflicting,
            )

        if len(inferred_capabilities) == 1:
            capability = next(iter(inferred_capabilities))
            return self._build_resolution(
                capability=capability,
                claims=inferred_claims,
                element_id=element_id,
                reason=(
                    "Interaction capability inferred from available "
                    "semantic evidence."
                ),
            )

        return InteractionCapabilityResolution(
            capability=InteractionCapability.UNKNOWN,
            confidence=0.0,
            reason=(
                "Evidence does not establish a supported interaction "
                "capability."
            ),
        )

    def _claims_from_evidence(
        self,
        evidence: tuple[SemanticEvidence, ...],
    ) -> tuple[_CapabilityClaim, ...]:
        claims: list[_CapabilityClaim] = []

        for item in evidence:
            if not item.observed:
                continue

            if item.kind is EvidenceKind.INTERACTION_CAPABILITY:
                capability = self._parse_capability(item.value)

                if (
                    capability is None
                    or capability is InteractionCapability.UNKNOWN
                ):
                    continue

                claims.append(
                    _CapabilityClaim(
                        capability=capability,
                        evidence=item,
                        observed_capability=True,
                    )
                )
                continue

            if item.kind is EvidenceKind.CONTROL_TYPE:
                if self._normalize(item.value) == "button":
                    claims.append(
                        _CapabilityClaim(
                            capability=InteractionCapability.CLICKABLE,
                            evidence=item,
                            observed_capability=False,
                        )
                    )

        return tuple(claims)

    def _build_resolution(
        self,
        *,
        capability: InteractionCapability,
        claims: tuple[_CapabilityClaim, ...],
        element_id: str | None,
        reason: str,
    ) -> InteractionCapabilityResolution:

        strongest_by_source: dict[
            EvidenceSource,
            _CapabilityClaim,
        ] = {}

        for claim in claims:
            source = claim.evidence.source
            previous = strongest_by_source.get(source)

            if (
                previous is None
                or claim.evidence.confidence
                > previous.evidence.confidence
            ):
                strongest_by_source[source] = claim

        strongest_claims = tuple(
            strongest_by_source.values()
        )

        confidence = self._aggregate_confidence(
            claim.evidence.confidence
            for claim in strongest_claims
        )

        supporting_evidence = tuple(
            claim.evidence
            for claim in strongest_claims
        )

        supporting_sources = tuple(
            sorted(
                strongest_by_source,
                key=lambda source: source.value,
            )
        )

        return InteractionCapabilityResolution(
            capability=capability,
            confidence=confidence,
            candidate=SemanticCandidate(
                semantic_name=capability.value,
                confidence=confidence,
                evidence=supporting_evidence,
                element_id=(
                    next(
                        (
                            item.element_id
                            for item in supporting_evidence
                            if item.element_id
                        ),
                        element_id,
                    )
                ),
                reason=reason,
                metadata={
                    "supporting_sources": tuple(
                        source.value
                        for source in supporting_sources
                    ),
                    "evidence_count": len(supporting_evidence),
                },
            ),
            reason=reason,
            supporting_sources=supporting_sources,
        )

    @classmethod
    def _aggregate_confidence(
        cls,
        confidences,
    ) -> float:
        values = tuple(
            max(0.0, min(1.0, value))
            for value in confidences
        )

        if not values:
            return 0.0

        combined = 1.0 - prod(
            1.0 - value
            for value in values
        )

        return round(
            min(combined, cls.MAX_AGGREGATED_CONFIDENCE),
            6,
        )

    @staticmethod
    def _parse_capability(value):
        normalized = InteractionCapabilityResolver._normalize(value)

        for capability in InteractionCapability:
            if capability.value == normalized:
                return capability

        return None

    @staticmethod
    def _normalize(value) -> str:
        raw = getattr(value, "value", value)

        if not isinstance(raw, str):
            return ""

        return raw.strip().casefold()
