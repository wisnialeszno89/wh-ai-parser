from __future__ import annotations

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
from app.agent.platform.windows_com import (
    ensure_windows_sta,
)


class WindowsUIAutomationProvider(PerceptionProvider):
    """
    Generic Windows UI Automation perception provider.

    UIA identity remains inside metadata. The model-facing ScreenElement
    exposes only semantic information such as:

        kind
        label
        bounds
        interaction capability
        current value

    No coordinate or runtime identifier is used as a semantic target.
    """

    INTERACTIVE_CONTROL_TYPES = frozenset(
        {
            "button",
            "edit",
            "checkbox",
            "combobox",
            "hyperlink",
            "listitem",
            "menuitem",
            "radiobutton",
            "splitbutton",
            "tabitem",
            "treeitem",
        }
    )

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

        if self._desktop_factory is None:
            if __import__("os").name != "nt":
                return ()

        try:
            desktop = (
                self._desktop_factory()
                if self._desktop_factory is not None
                else self._default_desktop()
            )

            root_window = self._observed_window(
                desktop,
                observation,
            )
        except Exception:
            return ()

        expected_title = (
            observation.state.active_window_title
        )

        if expected_title:
            try:
                actual_title = root_window.window_text()
            except Exception:
                return ()

            if (
                actual_title.strip()
                != expected_title.strip()
            ):
                return ()

        window_rect = observation.metadata.get(
            "window_rect"
        )

        origin_x = int(
            getattr(
                window_rect,
                "left",
                0,
            )
        )

        origin_y = int(
            getattr(
                window_rect,
                "top",
                0,
            )
        )

        root_handle = self._int_value(
            observation.metadata.get(
                "window_handle"
            )
        )

        foreground_handle = self._int_value(
            observation.metadata.get(
                "foreground_window_handle"
            )
        )

        foreground_owner = self._int_value(
            observation.metadata.get(
                "foreground_root_owner_handle"
            )
        )

        windows = [
            (
                root_window,
                root_handle,
                False,
            )
        ]

        # Generic owned modal support.
        #
        # This lets the same provider see a native dialog belonging to
        # the currently observed application without any WindowHub-specific
        # knowledge.
        if (
            foreground_handle > 0
            and foreground_handle != root_handle
            and foreground_owner == root_handle
        ):
            try:
                dialog_spec = desktop.window(
                    handle=foreground_handle
                )
                wrapper = getattr(
                    dialog_spec,
                    "wrapper_object",
                    None,
                )
                dialog = (
                    wrapper()
                    if callable(wrapper)
                    else dialog_spec
                )

                windows.append(
                    (
                        dialog,
                        foreground_handle,
                        True,
                    )
                )
            except Exception:
                pass

        elements: list[ScreenElement] = []

        for window, window_handle, owned_modal in windows:
            try:
                descendants = tuple(
                    window.descendants()
                )
            except Exception:
                continue

            label_candidates = self._collect_text_labels(
                descendants
            )

            for item in descendants:
                element = self._to_screen_element(
                    item=item,
                    origin_x=origin_x,
                    origin_y=origin_y,
                    window_handle=window_handle,
                    owned_modal=owned_modal,
                    label_candidates=label_candidates,
                )

                if element is not None:
                    elements.append(element)

        return tuple(elements)

    @staticmethod
    def _default_desktop():
        ensure_windows_sta()

        from pywinauto import Desktop

        return Desktop(backend="uia")

    @classmethod
    def _observed_window(
        cls,
        desktop,
        observation: EnvironmentObservation,
    ):
        handle = cls._int_value(
            observation.metadata.get(
                "window_handle"
            )
        )

        if handle <= 0:
            raise RuntimeError(
                "Windows desktop observation does not contain a valid "
                "top-level window handle."
            )

        spec = desktop.window(
            handle=handle
        )

        wrapper = getattr(
            spec,
            "wrapper_object",
            None,
        )

        return (
            wrapper()
            if callable(wrapper)
            else spec
        )

    def _to_screen_element(
        self,
        *,
        item,
        origin_x: int,
        origin_y: int,
        window_handle: int,
        owned_modal: bool,
        label_candidates,
    ) -> ScreenElement | None:

        try:
            info = item.element_info

            name = self._string(
                getattr(info, "name", None)
            )

            control_type = self._normalize_control_type(
                getattr(
                    info,
                    "control_type",
                    None,
                )
            )

            automation_id = self._string(
                getattr(
                    info,
                    "automation_id",
                    None,
                )
            )

            enabled = bool(
                getattr(
                    info,
                    "enabled",
                    False,
                )
            )

            visible = bool(
                getattr(
                    info,
                    "visible",
                    True,
                )
            )

            rectangle = item.rectangle()

        except Exception:
            return None

        if not visible:
            return None

        if (
            control_type
            not in self.INTERACTIVE_CONTROL_TYPES
        ):
            return None

        label = (
            name
            or self._neighbor_label(
                rectangle,
                label_candidates,
                control_type,
            )
        )

        if not label:
            return None

        left = int(rectangle.left) - origin_x
        top = int(rectangle.top) - origin_y
        width = int(rectangle.width())
        height = int(rectangle.height())

        if width <= 0 or height <= 0:
            return None

        runtime_id = self._runtime_id(item)

        element_id = (
            f"uia:{runtime_id}"
            if runtime_id
            else (
                f"uia:auto:{automation_id}"
                if automation_id
                else f"uia:name:{label.casefold()}"
            )
        )

        capability = (
            InteractionCapability.CLICKABLE
            if enabled
            else InteractionCapability.NOT_INTERACTIVE
        )

        current_value = (
            self._current_value(item)
        )

        metadata = {
            "source": "windows_ui_automation",
            "provider_element_id": element_id,
            "semantic_name": label,
            "name": name,
            "automation_id": automation_id,
            "uia_control_type": control_type,
            "uia_enabled": enabled,
            "uia_visible": visible,
            "uia_runtime_id": runtime_id,
            "current_value": current_value,
            "window_handle": (
                window_handle
                if window_handle > 0
                else None
            ),
            "uia_owned_modal": owned_modal,
            "interaction_capability_confidence": 0.99,
        }

        evidence = (
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
                    left,
                    top,
                    width,
                    height,
                ),
                confidence=0.99,
                element_id=element_id,
            ),
        )

        return ScreenElement(
            kind=control_type,
            label=label,
            x=left,
            y=top,
            width=width,
            height=height,
            confidence=0.99,
            metadata=metadata,
            interaction_capability=capability,
            evidence=evidence,
        )

    @staticmethod
    def _collect_text_labels(
        descendants,
    ) -> tuple:
        labels = []

        for item in descendants:
            try:
                info = item.element_info
                control_type = (
                    WindowsUIAutomationProvider
                    ._normalize_control_type(
                        getattr(
                            info,
                            "control_type",
                            None,
                        )
                    )
                )

                if control_type != "text":
                    continue

                name = (
                    WindowsUIAutomationProvider
                    ._string(
                        getattr(
                            info,
                            "name",
                            None,
                        )
                    )
                )

                if not name:
                    continue

                rectangle = item.rectangle()

                labels.append(
                    (
                        name,
                        int(rectangle.left),
                        int(rectangle.top),
                        int(rectangle.width()),
                        int(rectangle.height()),
                    )
                )

            except Exception:
                continue

        return tuple(labels)

    @staticmethod
    def _neighbor_label(
        rectangle,
        candidates,
        control_type,
    ) -> str | None:

        if control_type not in {
            "edit",
            "combobox",
        }:
            return None

        try:
            left = int(rectangle.left)
            top = int(rectangle.top)
            width = int(rectangle.width())
            height = int(rectangle.height())
        except Exception:
            return None

        center_y = top + height / 2

        ranked = []

        for (
            label,
            label_left,
            label_top,
            label_width,
            label_height,
        ) in candidates:

            label_center_y = (
                label_top + label_height / 2
            )

            vertical_distance = abs(
                center_y - label_center_y
            )

            horizontal_distance = (
                left
                - (label_left + label_width)
            )

            if horizontal_distance < -20:
                continue

            if horizontal_distance > 350:
                continue

            if vertical_distance > 80:
                continue

            ranked.append(
                (
                    vertical_distance
                    + max(
                        horizontal_distance,
                        0,
                    ) * 0.25,
                    label,
                )
            )

        if not ranked:
            return None

        ranked.sort(
            key=lambda value: value[0]
        )

        if (
            len(ranked) > 1
            and abs(
                ranked[1][0]
                - ranked[0][0]
            ) < 10
        ):
            return None

        return ranked[0][1]

    @staticmethod
    def _current_value(item):
        try:
            value = getattr(
                item.element_info,
                "rich_text",
                None,
            )
            value = (
                value.strip()
                if isinstance(value, str)
                else value
            )

            if value:
                return value
        except Exception:
            pass

        getter = getattr(
            item,
            "get_value",
            None,
        )

        if callable(getter):
            try:
                value = getter()

                if isinstance(value, str):
                    return value
            except Exception:
                pass

        return None

    @staticmethod
    def _runtime_id(item) -> str | None:
        try:
            value = getattr(
                item.element_info,
                "runtime_id",
                None,
            )
        except Exception:
            return None

        if value is None:
            return None

        if isinstance(
            value,
            (tuple, list),
        ):
            return "-".join(
                str(part)
                for part in value
            )

        return str(value)

    @staticmethod
    def _normalize_control_type(value) -> str:
        value = getattr(
            value,
            "value",
            value,
        )

        if not isinstance(value, str):
            return ""

        return value.strip().casefold()

    @staticmethod
    def _string(value) -> str | None:
        if not isinstance(value, str):
            return None

        value = value.strip()

        return value or None

    @staticmethod
    def _int_value(value) -> int:
        try:
            return int(value or 0)
        except (TypeError, ValueError):
            return 0
