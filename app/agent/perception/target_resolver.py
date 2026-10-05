from dataclasses import dataclass

from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.screen_scene import ScreenScene


@dataclass(frozen=True)
class TargetResolution:
    """
    Result of resolving a semantic target against a screen scene.
    """

    resolved: bool

    element: ScreenElement | None = None

    reason: str = ""

    score: float = 0.0


class TargetResolver:
    """
    Resolves a requested target against the current ScreenScene.

    v1 intentionally uses only deterministic information already
    present in ScreenElement.

    Semantic vision/reasoning will be added later without changing
    the resolver contract.
    """

    def resolve(
        self,
        scene: ScreenScene,
        target: str,
    ) -> TargetResolution:

        normalized = target.strip().casefold()

        if not normalized:
            return TargetResolution(
                resolved=False,
                reason="Target description is empty.",
            )

        exact_id = [
            element
            for element in scene.elements
            if (
                element.metadata is not None
                and isinstance(
                    element.metadata.get("tracked_object_id"),
                    str,
                )
                and element.metadata[
                    "tracked_object_id"
                ].casefold()
                == normalized
            )
        ]

        if len(exact_id) == 1:
            return TargetResolution(
                resolved=True,
                element=exact_id[0],
                reason="Exact tracked object id match.",
                score=1.0,
            )

        if len(exact_id) > 1:
            return TargetResolution(
                resolved=False,
                reason=(
                    "Multiple screen elements matched the "
                    "tracked object id."
                ),
            )

        exact = [
            element
            for element in scene.elements
            if (
                element.label is not None
                and element.label.casefold() == normalized
            )
        ]

        if len(exact) == 1:
            return TargetResolution(
                resolved=True,
                element=exact[0],
                reason="Exact screen element label match.",
                score=1.0,
            )

        if len(exact) > 1:
            return TargetResolution(
                resolved=False,
                reason=(
                    "Multiple screen elements matched the target "
                    "exactly."
                ),
            )

        semantic = [
            element
            for element in scene.elements
            if self._matches_metadata(
                element,
                normalized,
            )
        ]

        if len(semantic) == 1:
            return TargetResolution(
                resolved=True,
                element=semantic[0],
                reason="Semantic metadata match.",
                score=0.8,
            )

        if len(semantic) > 1:
            return TargetResolution(
                resolved=False,
                reason=(
                    "Multiple screen elements matched the target "
                    "through metadata."
                ),
            )

        return TargetResolution(
            resolved=False,
            reason=(
                "No visible screen element matched the target."
            ),
        )

    @staticmethod
    def _matches_metadata(
        element: ScreenElement,
        target: str,
    ) -> bool:

        metadata = element.metadata

        if not metadata:
            return False

        for key in (
            "name",
            "label",
            "semantic_label",
            "semantic_name",
            "description",
            "role",
        ):
            value = metadata.get(key)

            if (
                isinstance(value, str)
                and value.casefold() == target
            ):
                return True

        return False
