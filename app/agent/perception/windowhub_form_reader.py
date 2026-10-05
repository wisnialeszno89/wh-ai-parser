from __future__ import annotations

from dataclasses import dataclass

from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.screen_scene import ScreenScene


@dataclass(frozen=True)
class WindowHubFormField:
    """Read-only observation of one WindowHub form field."""

    label: str
    value: str | None
    control_type: str
    document_scope: str | None
    scope_status: str
    confidence: float | None
    element: ScreenElement


class WindowHubFormReader:
    """
    Extracts the currently observed WindowHub form fields.

    This class is deliberately read-only. It never resolves or executes
    actions and never invents document scope.
    """

    FIELD_CONTROL_TYPES = frozenset({
        "edit",
        "combobox",
    })

    def read(
        self,
        scene: ScreenScene,
    ) -> tuple[WindowHubFormField, ...]:
        active_document = scene.active_document
        fields = []

        for element in scene.elements:
            if element.kind.casefold() not in self.FIELD_CONTROL_TYPES:
                continue

            label = element.label.strip() if isinstance(element.label, str) else ""
            if not label:
                continue

            metadata = element.metadata or {}
            scope = self._document_scope(element)

            if active_document is not None:
                if scope == active_document:
                    scope_status = "active_document"
                elif scope is None:
                    scope_status = "unknown"
                else:
                    scope_status = "other_document"
            else:
                scope_status = "unresolved"

            fields.append(
                WindowHubFormField(
                    label=label,
                    value=self._current_value(element),
                    control_type=element.kind.casefold(),
                    document_scope=scope,
                    scope_status=scope_status,
                    confidence=element.confidence,
                    element=element,
                )
            )

        return tuple(fields)

    def read_active_document(
        self,
        scene: ScreenScene,
    ) -> tuple[WindowHubFormField, ...]:
        """
        Return only fields proven to belong to the resolved active document.

        If the active document is not resolved, no fields are returned.
        This prevents a read operation from silently mixing documents.
        """
        active_document = scene.active_document
        if active_document is None:
            return ()

        return tuple(
            field
            for field in self.read(scene)
            if field.scope_status == "active_document"
        )

    @staticmethod
    def _document_scope(element: ScreenElement) -> str | None:
        value = (element.metadata or {}).get("document_scope")
        if isinstance(value, str) and value.strip():
            return value.strip()
        return None

    @staticmethod
    def _current_value(element: ScreenElement) -> str | None:
        value = (element.metadata or {}).get("current_value")
        if isinstance(value, str):
            return value
        return None
