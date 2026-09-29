from dataclasses import dataclass

from app.agent.perception.interaction_capability import (
    InteractionCapability,
)
from app.agent.perception.semantic_evidence import (
    EvidenceKind,
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


class InteractionCapabilityResolver:
    """
    Resolve interaction capability from the existing SemanticEvidence model.

    The resolver intentionally starts conservative:
    - explicit observed capability evidence wins when unambiguous
    - BUTTON control-type evidence can infer CLICKABLE
    - ICON and all other currently known visual types remain UNKNOWN
    - conflicting explicit evidence remains UNKNOWN

    This class contains semantic inference only. It does not authorize
    actions and does not bypass SafetyGate.
    """

    def resolve(
        self,
        evidence: tuple[SemanticEvidence, ...],
        *,
        element_id: str | None = None,
    ) -> InteractionCapabilityResolution:

        explicit = tuple(
            item
            for item in evidence
            if (
                item.observed
                and item.kind is EvidenceKind.INTERACTION_CAPABILITY
            )
        )

        explicit_values = {
            self._parse_capability(item.value)
            for item in explicit
        }

        explicit_values.discard(None)

        if len(explicit_values) > 1:
            return InteractionCapabilityResolution(
                capability=InteractionCapability.UNKNOWN,
                confidence=0.0,
                reason="Conflicting observed interaction capability evidence.",
            )

        if len(explicit_values) == 1:
            capability = next(iter(explicit_values))
            strongest = max(
                explicit,
                key=lambda item: item.confidence,
            )
            return InteractionCapabilityResolution(
                capability=capability,
                confidence=strongest.confidence,
                candidate=SemanticCandidate(
                    semantic_name=capability.value,
                    confidence=strongest.confidence,
                    evidence=explicit,
                    element_id=(
                        strongest.element_id or element_id
                    ),
                    reason="Observed interaction capability evidence.",
                ),
                reason="Observed interaction capability evidence.",
            )

        control_type_evidence = tuple(
            item
            for item in evidence
            if (
                item.observed
                and item.kind is EvidenceKind.CONTROL_TYPE
            )
        )

        button_evidence = tuple(
            item
            for item in control_type_evidence
            if self._normalize(item.value) == "button"
        )

        if button_evidence:
            strongest = max(
                button_evidence,
                key=lambda item: item.confidence,
            )
            return InteractionCapabilityResolution(
                capability=InteractionCapability.CLICKABLE,
                confidence=strongest.confidence,
                candidate=SemanticCandidate(
                    semantic_name=InteractionCapability.CLICKABLE.value,
                    confidence=strongest.confidence,
                    evidence=button_evidence,
                    element_id=(
                        strongest.element_id or element_id
                    ),
                    reason="Button control type implies click capability.",
                ),
                reason="Button control type implies click capability.",
            )

        return InteractionCapabilityResolution(
            capability=InteractionCapability.UNKNOWN,
            confidence=0.0,
            reason="Evidence does not establish a supported interaction capability.",
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
