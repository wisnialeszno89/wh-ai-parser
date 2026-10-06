from __future__ import annotations

from dataclasses import dataclass

from app.agent.adapters.application_adapter import (
    AdapterDescriptor,
    ApplicationAdapter,
)


@dataclass(frozen=True)
class AdapterMatch:
    adapter: ApplicationAdapter
    score: float
    reasons: tuple[str, ...] = ()


class AdapterRegistry:
    """
    Deterministic registry for semantic application adapters.

    Resolution is fail-closed: if more than one adapter has the same best
    score, no adapter is selected.
    """

    def __init__(
        self,
        adapters: tuple[ApplicationAdapter, ...] = (),
    ) -> None:
        self._adapters: dict[str, ApplicationAdapter] = {}

        for adapter in adapters:
            self.register(adapter)

    def register(self, adapter: ApplicationAdapter) -> None:
        if not isinstance(adapter, ApplicationAdapter):
            raise TypeError(
                "Registered adapter must implement ApplicationAdapter."
            )

        adapter_id = adapter.descriptor.adapter_id.strip()
        if not adapter_id:
            raise ValueError("Adapter id must not be empty.")

        if adapter_id in self._adapters:
            raise ValueError(
                f"Adapter '{adapter_id}' is already registered."
            )

        self._adapters[adapter_id] = adapter

    def unregister(self, adapter_id: str) -> ApplicationAdapter | None:
        return self._adapters.pop(adapter_id, None)

    def all(self) -> tuple[ApplicationAdapter, ...]:
        return tuple(
            self._adapters[key]
            for key in sorted(self._adapters)
        )

    def resolve(
        self,
        *,
        application: str | None = None,
        capability: str | None = None,
    ) -> ApplicationAdapter | None:
        matches = self.matches(
            application=application,
            capability=capability,
        )

        if not matches:
            return None

        best_score = matches[0].score
        best = tuple(
            match
            for match in matches
            if match.score == best_score
        )

        if len(best) != 1:
            return None

        return best[0].adapter

    def matches(
        self,
        *,
        application: str | None = None,
        capability: str | None = None,
    ) -> tuple[AdapterMatch, ...]:
        requested_application = (
            application.strip().casefold()
            if isinstance(application, str) and application.strip()
            else None
        )
        requested_capability = (
            capability.strip().casefold()
            if isinstance(capability, str) and capability.strip()
            else None
        )

        results: list[AdapterMatch] = []

        for adapter in self._adapters.values():
            descriptor = adapter.descriptor
            score = 0.0
            reasons: list[str] = []

            descriptor_application = (
                descriptor.application.strip().casefold()
            )

            if requested_application is not None:
                if descriptor_application != requested_application:
                    continue
                score += 2.0
                reasons.append("application")

            if requested_capability is not None:
                if not adapter.supports(requested_capability):
                    continue
                score += 1.0
                reasons.append("capability")

            if not adapter.is_available():
                continue

            score += 0.1
            reasons.append("available")

            results.append(
                AdapterMatch(
                    adapter=adapter,
                    score=score,
                    reasons=tuple(reasons),
                )
            )

        results.sort(
            key=lambda item: (
                -item.score,
                item.adapter.descriptor.adapter_id,
            )
        )

        return tuple(results)

    def describe(self) -> tuple[AdapterDescriptor, ...]:
        return tuple(
            adapter.descriptor
            for adapter in self.all()
        )
