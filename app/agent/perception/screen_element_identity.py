from dataclasses import dataclass

from app.agent.perception.screen_element import ScreenElement


@dataclass(frozen=True)
class ScreenElementIdentity:
    """
    Stable semantic identity hints for a ScreenElement.

    Identity is intentionally separate from geometry and interaction
    capability so provider fusion can remain conservative.
    """

    source: str | None = None
    provider_id: str | None = None
    semantic_name: str | None = None
    tracked_object_id: str | None = None
    label: str | None = None

    @property
    def has_strong_identity(self) -> bool:
        return any(
            value
            for value in (
                self.tracked_object_id,
                self.provider_id,
                self.semantic_name,
                self.label,
            )
        )


class ScreenElementIdentityResolver:
    """
    Extract identity hints from a ScreenElement.

    v1 uses explicit provider/semantic identifiers only.
    It deliberately does not infer identity from geometry alone.
    """

    def resolve(self, element: ScreenElement) -> ScreenElementIdentity:
        metadata = element.metadata or {}

        source = self._string(metadata.get("source"))
        tracked_object_id = self._string(
            metadata.get("tracked_object_id")
        )
        provider_id = self._string(
            metadata.get("provider_element_id")
        )
        semantic_name = self._first_string(
            metadata,
            (
                "semantic_name",
                "name",
                "semantic_label",
                "description",
                "role",
            ),
        )
        label = self._string(element.label)

        return ScreenElementIdentity(
            source=source,
            provider_id=provider_id,
            semantic_name=semantic_name,
            tracked_object_id=tracked_object_id,
            label=label,
        )

    @staticmethod
    def _first_string(metadata, keys):
        for key in keys:
            value = ScreenElementIdentityResolver._string(
                metadata.get(key)
            )
            if value:
                return value
        return None

    @staticmethod
    def _string(value):
        if not isinstance(value, str):
            return None

        normalized = value.strip()
        return normalized or None
