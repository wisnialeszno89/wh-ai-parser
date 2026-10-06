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

        exact_resolution = self._resolve_scoped_candidates(
            scene=scene,
            candidates=exact,
            match_reason="Exact screen element label match.",
        )

        if exact_resolution is not None:
            return exact_resolution

        semantic = [
            element
            for element in scene.elements
            if self._matches_metadata(
                element,
                normalized,
            )
        ]

        semantic_resolution = self._resolve_scoped_candidates(
            scene=scene,
            candidates=semantic,
            match_reason="Semantic metadata match.",
            score=0.8,
        )

        if semantic_resolution is not None:
            return semantic_resolution

        return TargetResolution(
            resolved=False,
            reason=(
                "No visible screen element matched the target."
            ),
        )

    @classmethod
    def _resolve_scoped_candidates(
        cls,
        *,
        scene: ScreenScene,
        candidates: list[ScreenElement],
        match_reason: str,
        score: float = 1.0,
    ) -> TargetResolution | None:
        """
        Resolve candidates with the scene's active document context.

        Scope is applied only when the scene has a resolved active document.
        An element is eligible for scoped resolution only when it carries an
        explicit document_scope equal to that active document.

        Missing scope evidence never becomes a guess.
        """
        if not candidates:
            return None

        active_document = scene.active_document

        if active_document is None:
            if len(candidates) == 1:
                return TargetResolution(
                    resolved=True,
                    element=candidates[0],
                    reason=match_reason,
                    score=score,
                )

            return TargetResolution(
                resolved=False,
                reason=(
                    "Multiple screen elements matched the target, but "
                    "the active document is not reliably resolved."
                ),
            )

        scoped = [
            element
            for element in candidates
            if cls._document_scope(element) == active_document
        ]

        # Owned modal dialogs are an explicit execution scope of their own.
        # A modal control such as "Okno" or "Dalej >" belongs to the current
        # workflow dialog, not to the active document tab, so document scope
        # must not reject an otherwise unique modal candidate.
        modal = [
            element
            for element in candidates
            if (
                isinstance(element.metadata, dict)
                and element.metadata.get("uia_owned_modal") is True
            )
        ]

        if len(modal) == 1:
            return TargetResolution(
                resolved=True,
                element=modal[0],
                reason=(
                    f"{match_reason} Owned WindowHub modal scope "
                    "matched."
                ),
                score=score,
            )

        if len(scoped) == 1:
            return TargetResolution(
                resolved=True,
                element=scoped[0],
                reason=(
                    f"{match_reason} Active document scope "
                    f"'{active_document}' matched."
                ),
                score=score,
            )

        if len(scoped) > 1:
            return TargetResolution(
                resolved=False,
                reason=(
                    "Multiple screen elements matched the target "
                    f"inside active document '{active_document}'."
                ),
            )

        # A unique candidate without explicit scope remains safe to resolve:
        # there is no competing element to distinguish. Scope becomes a
        # mandatory discriminator only when multiple candidates exist.
        unscoped = [
            element
            for element in candidates
            if cls._document_scope(element) is None
        ]

        if len(candidates) == 1 and len(unscoped) == 1:
            return TargetResolution(
                resolved=True,
                element=unscoped[0],
                reason=(
                    f"{match_reason} No competing target required "
                    "document scope."
                ),
                score=score,
            )

        return TargetResolution(
            resolved=False,
            reason=(
                f"Target matched outside active document "
                f"'{active_document}', or no explicit document scope "
                "was observed for a competing target."
            ),
        )

    @staticmethod
    def _document_scope(element: ScreenElement) -> str | None:
        metadata = element.metadata or {}
        value = metadata.get("document_scope")

        if isinstance(value, str) and value.strip():
            return value.strip()

        return None

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
