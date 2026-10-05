from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from app.agent.environment.environment_observation import (
    EnvironmentObservation,
)
from app.agent.perception.screen_scene import ScreenScene


@dataclass(frozen=True)
class WindowHubDocumentContent:
    """Read-only content exposed by one WindowHub document RichTextBox."""

    document_scope: str
    value: str
    control_type: str
    class_name: str


class WindowHubDocumentReader:
    """
    Reads WindowHub document content exposed through UI Automation.

    WindowHub does not expose the visible offer body as Edit/ComboBox
    controls. In observed offers it exposes document content as a
    RichTextBox-backed UIA Document control. This reader therefore stays
    separate from WindowHubFormReader.

    The reader is strictly read-only. It never clicks, focuses, types,
    selects, saves, or otherwise mutates WindowHub.
    """

    def __init__(
        self,
        *,
        desktop_factory: Callable[[], object] | None = None,
    ) -> None:
        self._desktop_factory = desktop_factory

    def read(self, scene: ScreenScene) -> tuple[WindowHubDocumentContent, ...]:
        active_document = scene.active_document
        if active_document is None:
            return ()

        observation = scene.observation

        try:
            desktop = (
                self._desktop_factory()
                if self._desktop_factory is not None
                else self._default_desktop()
            )
            window = self._active_window(desktop, observation)
        except Exception:
            return ()

        try:
            descendants = tuple(window.descendants())
        except Exception:
            return ()

        results = []

        for item in descendants:
            document = self._read_document(item, active_document)
            if document is not None:
                results.append(document)

        return tuple(results)

    @staticmethod
    def _default_desktop():
        from pywinauto import Desktop

        return Desktop(backend="uia")

    @staticmethod
    def _active_window(desktop, observation: EnvironmentObservation):
        window_handle = observation.metadata.get("window_handle")
        if window_handle is None:
            raise RuntimeError("WindowHub window handle was not observed.")

        handle = int(window_handle)
        if handle <= 0:
            raise RuntimeError("Invalid WindowHub window handle.")

        return desktop.window(handle=handle).wrapper_object()

    @classmethod
    def _read_document(
        cls,
        item,
        active_document: str,
    ) -> WindowHubDocumentContent | None:
        try:
            info = item.element_info
            control_type = str(
                getattr(info, "control_type", "") or ""
            ).strip()
            class_name = str(
                getattr(info, "class_name", "") or ""
            ).strip()
        except Exception:
            return None

        if control_type.casefold() != "document":
            return None

        value = cls._value(item)
        if not value:
            return None

        scope = cls._document_window_scope(item)
        if scope != active_document:
            return None

        return WindowHubDocumentContent(
            document_scope=scope,
            value=value,
            control_type=control_type,
            class_name=class_name,
        )

    @staticmethod
    def _value(item) -> str | None:
        for method_name in ("get_value", "window_text"):
            method = getattr(item, method_name, None)
            if not callable(method):
                continue

            try:
                value = method()
            except Exception:
                continue

            if isinstance(value, str) and value.strip():
                return value.strip()

        info = getattr(item, "element_info", None)
        for attribute_name in ("value", "legacy_value", "rich_text"):
            value = getattr(info, attribute_name, None)
            if isinstance(value, str) and value.strip():
                return value.strip()

        return None

    @classmethod
    def _document_window_scope(cls, item) -> str | None:
        current = item

        for _ in range(12):
            parent_getter = getattr(current, "parent", None)
            if not callable(parent_getter):
                return None

            try:
                current = parent_getter()
            except Exception:
                return None

            if current is None:
                return None

            try:
                info = current.element_info
                control_type = str(
                    getattr(info, "control_type", "") or ""
                ).strip().casefold()
                name = str(
                    getattr(info, "name", "") or ""
                ).strip()
            except Exception:
                return None

            if control_type == "window" and name:
                return name

        return None
