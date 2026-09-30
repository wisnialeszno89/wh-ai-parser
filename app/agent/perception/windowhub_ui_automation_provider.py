from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from app.agent.environment.environment_observation import (
    EnvironmentObservation,
)
from app.agent.perception.interaction_capability import (
    InteractionCapability,
)
from app.agent.perception.perception_provider import (
    PerceptionProvider,
)
from app.agent.perception.screen_element import (
    ScreenElement,
)
from app.agent.perception.semantic_evidence import (
    EvidenceKind,
    EvidenceSource,
    SemanticEvidence,
)


@dataclass(frozen=True)
class _UIARect:
    left: int
    top: int
    width: int
    height: int

    @property
    def right(self) -> int:
        return self.left + self.width

    @property
    def bottom(self) -> int:
        return self.top + self.height

    @property
    def center(self) -> tuple[int, int]:
        return (
            self.left + self.width // 2,
            self.top + self.height // 2,
        )


class WindowHubUIAutomationProvider(PerceptionProvider):
    """
    WindowHub semantic provider backed by Windows UI Automation.

    UIA supplies semantic identity such as Name, AutomationId and
    ControlType. It does not execute actions.

    When the visual provider has already populated
    observation.metadata["execution_runtime"], this provider performs
    a conservative WindowHub-specific correlation: a named interactive
    UIA element may be associated with exactly one tracked visual object
    whose center lies inside the UIA bounds. Ambiguous matches are left
    without a tracked_object_id and therefore cannot silently authorize
    execution.

    This provider is intentionally Windows-specific. Universal Core only
    consumes the resulting ScreenElement contract.
    """

    INTERACTIVE_CONTROL_TYPES = frozenset({
        "button",
        "checkbox",
        "combobox",
        "hyperlink",
        "listitem",
        "menuitem",
        "radiobutton",
        "splitbutton",
        "tabitem",
        "treeitem",
    })

    def __init__(
        self,
        *,
        desktop_factory: Callable[[], object] | None = None,
    ) -> None:
        self._desktop_factory = desktop_factory

    def perceive(
        self,
        observation: EnvironmentObservation,
    ) -> tuple[ScreenElement, ...]:
        if self._desktop_factory is None and __import__("os").name != "nt":
            return ()

        try:
            desktop = (
                self._desktop_factory()
                if self._desktop_factory is not None
                else self._default_desktop()
            )
            window = desktop.get_active()
        except Exception:
            return ()

        expected_title = observation.state.active_window_title
        if expected_title:
            try:
                if window.window_text() != expected_title:
                    return ()
            except Exception:
                return ()

        window_rect = observation.metadata.get("window_rect")
        origin_x = int(getattr(window_rect, "left", 0))
        origin_y = int(getattr(window_rect, "top", 0))

        tracked_objects = self._tracked_objects(observation)

        elements: list[ScreenElement] = []

        try:
            descendants = window.descendants()
        except Exception:
            return ()

        for item in descendants:
            element = self._to_screen_element(
                item=item,
                origin_x=origin_x,
                origin_y=origin_y,
                tracked_objects=tracked_objects,
            )
            if element is not None:
                elements.append(element)

        return tuple(elements)

    @staticmethod
    def _default_desktop():
        from pywinauto import Desktop

        return Desktop(backend="uia")

    @staticmethod
    def _tracked_objects(observation):
        runtime = observation.metadata.get("execution_runtime")
        if not isinstance(runtime, dict):
            return ()

        value = runtime.get("robot_tracked_objects")
        if not isinstance(value, tuple):
            return ()

        return value

    def _to_screen_element(
        self,
        *,
        item,
        origin_x: int,
        origin_y: int,
        tracked_objects,
    ) -> ScreenElement | None:
        try:
            name = self._string(
                getattr(item.element_info, "name", None)
            )
            automation_id = self._string(
                getattr(item.element_info, "automation_id", None)
            )
            control_type = self._normalize_control_type(
                getattr(item.element_info, "control_type", None)
            )
            enabled = bool(
                getattr(item.element_info, "enabled", False)
            )
            visible = bool(
                getattr(item.element_info, "visible", True)
            )
            rectangle = item.rectangle()
            runtime_id = self._runtime_id(item)
        except Exception:
            return None

        if not visible or not (name or automation_id):
            return None

        if control_type not in self.INTERACTIVE_CONTROL_TYPES:
            return None

        rect = _UIARect(
            left=int(rectangle.left) - origin_x,
            top=int(rectangle.top) - origin_y,
            width=int(rectangle.width()),
            height=int(rectangle.height()),
        )

        if rect.width <= 0 or rect.height <= 0:
            return None

        label = name or automation_id
        capability = (
            InteractionCapability.CLICKABLE
            if enabled
            else InteractionCapability.NOT_INTERACTIVE
        )

        element_id = (
            f"uia:{runtime_id}"
            if runtime_id
            else (
                f"uia:auto:{automation_id}"
                if automation_id
                else f"uia:name:{label.casefold()}"
            )
        )

        tracked_id = self._correlate_tracked_object(
            rect,
            tracked_objects,
        )

        evidence = [
            SemanticEvidence(
                source=EvidenceSource.ACCESSIBILITY,
                kind=EvidenceKind.LABEL,
                value=label,
                confidence=0.99,
                element_id=element_id,
            ),
            SemanticEvidence(
                source=EvidenceSource.ACCESSIBILITY,
                kind=EvidenceKind.ROLE,
                value=control_type,
                confidence=0.99,
                element_id=element_id,
            ),
            SemanticEvidence(
                source=EvidenceSource.ACCESSIBILITY,
                kind=EvidenceKind.INTERACTION_CAPABILITY,
                value=capability.value,
                confidence=0.99,
                element_id=element_id,
            ),
            SemanticEvidence(
                source=EvidenceSource.ACCESSIBILITY,
                kind=EvidenceKind.BOUNDS,
                value=(
                    rect.left,
                    rect.top,
                    rect.width,
                    rect.height,
                ),
                confidence=0.99,
                element_id=element_id,
            ),
        ]

        metadata = {
            "source": "windowhub_ui_automation",
            "provider_element_id": element_id,
            "semantic_name": label,
            "name": name,
            "automation_id": automation_id,
            "uia_control_type": control_type,
            "uia_enabled": enabled,
            "uia_visible": visible,
            "uia_runtime_id": runtime_id,
            "correlation": (
                "unique_visual_center_inside_uia_bounds"
                if tracked_id
                else "unresolved"
            ),
            "interaction_capability": capability.value,
            "interaction_capability_confidence": 0.99,
            "semantic_evidence": tuple(evidence),
        }

        if tracked_id:
            metadata["tracked_object_id"] = tracked_id

        return ScreenElement(
            kind=control_type,
            label=label,
            x=rect.left,
            y=rect.top,
            width=rect.width,
            height=rect.height,
            confidence=0.99,
            metadata=metadata,
            interaction_capability=capability,
            evidence=tuple(evidence),
        )

    @staticmethod
    def _correlate_tracked_object(
        rect: _UIARect,
        tracked_objects,
    ) -> str | None:
        candidates = []

        for tracked in tracked_objects:
            if getattr(tracked, "status", None).value == "lost":
                continue

            bounds = getattr(
                getattr(tracked, "object", None),
                "bounds",
                None,
            )
            if bounds is None:
                continue

            center = bounds.center
            if (
                rect.left <= center[0] <= rect.right
                and rect.top <= center[1] <= rect.bottom
            ):
                candidates.append(tracked)

        if len(candidates) != 1:
            return None

        return candidates[0].id

    @staticmethod
    def _normalize_control_type(value) -> str:
        raw = getattr(value, "value", value)
        if not isinstance(raw, str):
            return ""
        return raw.strip().casefold()

    @staticmethod
    def _string(value) -> str | None:
        if not isinstance(value, str):
            return None
        value = value.strip()
        return value or None

    @staticmethod
    def _runtime_id(item) -> str | None:
        try:
            value = getattr(item.element_info, "runtime_id", None)
        except Exception:
            return None

        if value is None:
            return None

        if isinstance(value, (tuple, list)):
            return "-".join(str(part) for part in value)

        return str(value)
