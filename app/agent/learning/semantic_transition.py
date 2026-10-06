from __future__ import annotations

from dataclasses import dataclass

from app.agent.learning.semantic_snapshot import SemanticSnapshot


_STATE_KEYS = (
    "current_value",
    "uia_selected",
    "document_scope",
)

_INTERACTIVE_KINDS = {
    "button",
    "checkbox",
    "combobox",
    "edit",
    "hyperlink",
    "listitem",
    "menuitem",
    "radiobutton",
    "splitbutton",
    "tabitem",
    "textbox",
    "treeitem",
}

_DEFAULT_MAX_REQUIREMENTS = 6


@dataclass(frozen=True)
class SemanticTransition:
    """Compact, model-safe description of a learned state transition.

    A transition deliberately records only semantic state that is useful for
    replay verification. It does not copy the complete AFTER scene because a
    GUI may expose many implementation-specific controls that are irrelevant
    to the business transition.
    """

    application: str | None = None
    window_title: str | None = None
    active_document: str | None = None
    requirements: tuple[dict[str, object], ...] = ()

    @classmethod
    def from_snapshots(
        cls,
        before: SemanticSnapshot | None,
        after: SemanticSnapshot | None,
        *,
        max_requirements: int = _DEFAULT_MAX_REQUIREMENTS,
    ) -> "SemanticTransition":
        if max_requirements < 1:
            raise ValueError("max_requirements must be positive.")

        if after is None:
            return cls()

        return cls(
            application=after.application,
            window_title=after.window_title,
            active_document=after.active_document,
            requirements=cls._derive_requirements(
                before,
                after,
                max_requirements=max_requirements,
            ),
        )

    @staticmethod
    def _derive_requirements(
        before: SemanticSnapshot | None,
        after: SemanticSnapshot,
        *,
        max_requirements: int,
    ) -> tuple[dict[str, object], ...]:
        if before is None:
            return ()

        before_by_key: dict[tuple[str, str], list[dict[str, object]]] = {}
        for element in before.elements:
            key = SemanticTransition._element_key(element)
            before_by_key.setdefault(key, []).append(element)

        state_changes: list[dict[str, object]] = []
        appeared: list[dict[str, object]] = []

        for element in after.elements:
            key = SemanticTransition._element_key(element)
            candidates = before_by_key.get(key)

            if not candidates:
                if SemanticTransition._is_useful_appeared_element(element):
                    appeared.append(
                        SemanticTransition._requirement_from_element(element)
                    )
                continue

            before_element = candidates[0]
            changed = {
                state_key: element.get(state_key)
                for state_key in _STATE_KEYS
                if state_key in element
                and element.get(state_key) != before_element.get(state_key)
            }

            if changed:
                requirement = {
                    "kind": element.get("kind"),
                    "label": element.get("label"),
                }
                requirement.update(changed)
                state_changes.append(requirement)

        # State changes are stronger evidence than appearance. Keep them all
        # up to the cap, then use a few semantic anchors from newly visible UI.
        requirements = state_changes[:max_requirements]
        remaining = max_requirements - len(requirements)
        if remaining > 0:
            requirements.extend(appeared[:remaining])

        return tuple(requirements)

    @staticmethod
    def _element_key(element: dict[str, object]) -> tuple[str, str]:
        return (
            str(element.get("kind") or "").casefold(),
            str(element.get("label") or "").casefold(),
        )

    @staticmethod
    def _is_useful_appeared_element(
        element: dict[str, object],
    ) -> bool:
        kind = str(element.get("kind") or "").casefold()
        label = element.get("label")
        return kind in _INTERACTIVE_KINDS and isinstance(label, str) and bool(
            label.strip()
        )

    @staticmethod
    def _requirement_from_element(
        element: dict[str, object],
    ) -> dict[str, object]:
        requirement = {
            "kind": element.get("kind"),
            "label": element.get("label"),
        }
        for state_key in _STATE_KEYS:
            if state_key in element:
                requirement[state_key] = element.get(state_key)
        return requirement

    def to_payload(self) -> dict[str, object]:
        return {
            "application": self.application,
            "window_title": self.window_title,
            "active_document": self.active_document,
            "requirements": [dict(item) for item in self.requirements],
        }

    @classmethod
    def from_payload(
        cls,
        payload: dict[str, object],
    ) -> "SemanticTransition":
        raw_requirements = payload.get("requirements") or []
        if not isinstance(raw_requirements, list):
            raise ValueError("Semantic transition requirements must be a list.")

        requirements = tuple(
            dict(item)
            for item in raw_requirements
            if isinstance(item, dict)
        )

        return cls(
            application=(
                str(payload["application"])
                if payload.get("application") is not None
                else None
            ),
            window_title=(
                str(payload["window_title"])
                if payload.get("window_title") is not None
                else None
            ),
            active_document=(
                str(payload["active_document"])
                if payload.get("active_document") is not None
                else None
            ),
            requirements=requirements,
        )
