from dataclasses import dataclass

from app.agent.perception.interaction_capability import (
    InteractionCapability,
)
from app.agent.perception.interaction_capability_resolver import (
    InteractionCapabilityResolver,
)
from app.agent.perception.screen_element import (
    ScreenElement,
)
from app.agent.perception.screen_element_identity import (
    ScreenElementIdentity,
    ScreenElementIdentityResolver,
)
from app.agent.perception.semantic_evidence import (
    SemanticEvidence,
)


@dataclass(frozen=True)
class ScreenElementFusionResult:
    """
    Result of conservative provider fusion.

    Elements are merged only when the identity contract provides a
    sufficiently strong and unambiguous match.
    """

    elements: tuple[ScreenElement, ...]
    merged_group_count: int = 0


class ScreenElementFusion:
    """
    Merge ScreenElements from multiple perception providers.

    Matching policy:
    1. Same provider/source + same tracked_object_id.
    2. Cross-provider exact semantic_name, only when that identity is
       unique within each contributing provider.
    3. Cross-provider exact label, only when that identity is unique
       within each contributing provider.
    4. Otherwise keep elements separate.

    Geometry alone never creates identity.
    """

    def __init__(
        self,
        identity_resolver: ScreenElementIdentityResolver | None = None,
        capability_resolver: InteractionCapabilityResolver | None = None,
    ) -> None:
        self.identity_resolver = (
            identity_resolver
            if identity_resolver is not None
            else ScreenElementIdentityResolver()
        )
        self.capability_resolver = (
            capability_resolver
            if capability_resolver is not None
            else InteractionCapabilityResolver()
        )

    def fuse(
        self,
        elements: tuple[ScreenElement, ...],
    ) -> ScreenElementFusionResult:
        identities = tuple(
            self.identity_resolver.resolve(element)
            for element in elements
        )

        shared_id_counts = self._counts_by_source(
            identities,
            lambda identity: identity.shared_id,
        )
        tracked_object_id_counts = self._counts_by_source(
            identities,
            lambda identity: identity.tracked_object_id,
        )
        provider_id_counts = self._counts_by_source(
            identities,
            lambda identity: identity.provider_id,
        )
        semantic_counts = self._counts_by_source(
            identities,
            lambda identity: identity.semantic_name,
        )
        label_counts = self._counts_by_source(
            identities,
            lambda identity: identity.label,
        )

        groups: list[list[int]] = []

        for index, identity in enumerate(identities):
            match = self._find_match(
                index=index,
                identity=identity,
                identities=identities,
                shared_id_counts=shared_id_counts,
                tracked_object_id_counts=tracked_object_id_counts,
                provider_id_counts=provider_id_counts,
                semantic_counts=semantic_counts,
                label_counts=label_counts,
                groups=groups,
            )

            if match is None:
                groups.append([index])
            else:
                groups[match].append(index)

        fused = tuple(
            self._merge_group(
                tuple(elements[index] for index in group),
            )
            for group in groups
        )

        merged_group_count = sum(
            1
            for group in groups
            if len(group) > 1
        )

        return ScreenElementFusionResult(
            elements=fused,
            merged_group_count=merged_group_count,
        )

    def _find_match(
        self,
        *,
        index: int,
        identity: ScreenElementIdentity,
        identities: tuple[ScreenElementIdentity, ...],
        shared_id_counts,
        tracked_object_id_counts,
        provider_id_counts,
        semantic_counts,
        label_counts,
        groups: list[list[int]],
    ) -> int | None:
        element_source = self._source_for_identity(
            identity,
            index,
        )

        for group_index, group in enumerate(groups):
            representative_index = group[0]
            representative_identity = identities[representative_index]
            representative_source = self._source_for_identity(
                representative_identity,
                representative_index,
            )

            if (
                element_source == representative_source
                and self._safe_same_source_match(
                    identity.shared_id,
                    representative_identity.shared_id,
                    element_source,
                    shared_id_counts,
                )
            ):
                return group_index

            if (
                element_source == representative_source
                and self._safe_same_source_match(
                    identity.tracked_object_id,
                    representative_identity.tracked_object_id,
                    element_source,
                    tracked_object_id_counts,
                )
            ):
                return group_index

            if (
                element_source == representative_source
                and self._safe_same_source_match(
                    identity.provider_id,
                    representative_identity.provider_id,
                    element_source,
                    provider_id_counts,
                )
            ):
                return group_index

            if self._safe_cross_provider_match(
                identity.shared_id,
                representative_identity.shared_id,
                element_source,
                representative_source,
                shared_id_counts,
            ):
                return group_index

            if self._safe_cross_provider_match(
                identity.semantic_name,
                representative_identity.semantic_name,
                element_source,
                representative_source,
                semantic_counts,
            ):
                return group_index

            if self._safe_cross_provider_match(
                identity.label,
                representative_identity.label,
                element_source,
                representative_source,
                label_counts,
            ):
                return group_index

        return None

    @staticmethod
    def _safe_same_source_match(
        left_value: str | None,
        right_value: str | None,
        source: str,
        counts,
    ) -> bool:
        if (
            not left_value
            or not right_value
            or left_value.casefold()
            != right_value.casefold()
        ):
            return False

        return (
            counts.get(
                (source, left_value.casefold()),
                0,
            )
            == 1
        )

    @staticmethod
    def _safe_cross_provider_match(
        left_value: str | None,
        right_value: str | None,
        left_source: str,
        right_source: str,
        counts,
    ) -> bool:
        if (
            not left_value
            or not right_value
            or left_value.casefold()
            != right_value.casefold()
            or left_source == right_source
        ):
            return False

        return (
            counts.get(
                (left_source, left_value.casefold()),
                0,
            )
            == 1
            and counts.get(
                (right_source, right_value.casefold()),
                0,
            )
            == 1
        )

    @staticmethod
    def _counts_by_source(
        identities: tuple[ScreenElementIdentity, ...],
        getter,
    ):
        counts: dict[tuple[str, str], int] = {}

        for index, identity in enumerate(identities):
            value = getter(identity)
            if not value:
                continue

            source = ScreenElementFusion._source_for_identity(
                identity,
                index,
            )
            key = (source, value.casefold())
            counts[key] = counts.get(key, 0) + 1

        return counts

    @staticmethod
    def _source_for_identity(
        identity: ScreenElementIdentity,
        index: int,
    ) -> str:
        if identity.source:
            return identity.source

        if identity.provider_id:
            return f"provider:{identity.provider_id}"

        return f"anonymous:{index}"

    def _merge_group(
        self,
        elements: tuple[ScreenElement, ...],
    ) -> ScreenElement:
        primary = max(
            elements,
            key=lambda element: (
                element.confidence
                if element.confidence is not None
                else 0.0
            ),
        )

        evidence = self._merge_evidence(elements)

        capability_resolution = self.capability_resolver.resolve(
            evidence,
            element_id=self._element_id(primary),
        )

        metadata = dict(primary.metadata or {})

        for element in elements:
            for key, value in (element.metadata or {}).items():
                metadata.setdefault(key, value)

        metadata.update({
            "fused": len(elements) > 1,
            "fused_provider_count": len({
                self._provider_name(element, index)
                for index, element in enumerate(elements)
            }),
            "fused_element_count": len(elements),
            "interaction_capability": (
                capability_resolution.capability.value
            ),
            "interaction_capability_confidence": (
                capability_resolution.confidence
            ),
            "fusion_sources": tuple(
                sorted({
                    self._provider_name(element, index)
                    for index, element in enumerate(elements)
                })
            ),
        })

        label = next(
            (
                element.label
                for element in sorted(
                    elements,
                    key=lambda item: (
                        item.confidence
                        if item.confidence is not None
                        else 0.0
                    ),
                    reverse=True,
                )
                if element.label
            ),
            primary.label,
        )

        return ScreenElement(
            kind=primary.kind,
            label=label,
            x=primary.x,
            y=primary.y,
            width=primary.width,
            height=primary.height,
            confidence=primary.confidence,
            metadata=metadata,
            interaction_capability=(
                capability_resolution.capability
            ),
            evidence=evidence,
        )

    @staticmethod
    def _merge_evidence(
        elements: tuple[ScreenElement, ...],
    ) -> tuple[SemanticEvidence, ...]:
        merged: list[SemanticEvidence] = []
        seen: set[tuple[object, ...]] = set()

        for element in elements:
            for item in element.evidence:
                key = (
                    item.source,
                    item.kind,
                    repr(item.value),
                    item.confidence,
                    item.element_id,
                    item.observed,
                )
                if key in seen:
                    continue

                seen.add(key)
                merged.append(item)

        return tuple(merged)

    @staticmethod
    def _element_id(element: ScreenElement) -> str | None:
        metadata = element.metadata or {}
        value = metadata.get("tracked_object_id")

        if isinstance(value, str):
            return value

        return element.label

    @staticmethod
    def _provider_name(
        element: ScreenElement,
        index: int,
    ) -> str:
        metadata = element.metadata or {}
        value = metadata.get("source")

        if isinstance(value, str) and value.strip():
            return value.strip()

        return f"unknown:{index}"
