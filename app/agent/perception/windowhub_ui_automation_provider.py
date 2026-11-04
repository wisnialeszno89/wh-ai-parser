from __future__ import annotations

from collections.abc import Mapping
import time
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
    })

    # Tables are semantic read targets, never click/action targets.
    TABLE_CONTROL_TYPES = frozenset({
        "datagrid",
        "table",
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
            window = self._active_window(
                desktop,
                observation,
                allow_test_factory_fallback=(
                    self._desktop_factory is not None
                ),
            )
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
            descendants = tuple(window.descendants())
        except Exception:
            return ()

        label_candidates = self._collect_label_candidates(
            descendants,
            origin_x=origin_x,
            origin_y=origin_y,
        )

        for item in descendants:
            element = self._to_screen_element(
                item=item,
                origin_x=origin_x,
                origin_y=origin_y,
                tracked_objects=tracked_objects,
                label_candidates=label_candidates,
            )
            if element is not None:
                elements.append(element)

        return tuple(elements)

    @staticmethod
    def _default_desktop():
        from pywinauto import Desktop

        return Desktop(backend="uia")

    @staticmethod
    def _active_window(
        desktop,
        observation: EnvironmentObservation,
        *,
        allow_test_factory_fallback: bool,
    ):
        window_handle = observation.metadata.get("window_handle")
        if window_handle is not None:
            handle = int(window_handle)
            if handle <= 0:
                raise RuntimeError(
                    "Invalid observed WindowHub window handle."
                )
            window_spec = desktop.window(handle=handle)
            return window_spec.wrapper_object()

        if allow_test_factory_fallback:
            get_active = getattr(desktop, "get_active", None)
            if callable(get_active):
                return get_active()

        import ctypes

        user32 = ctypes.WinDLL("user32", use_last_error=True)
        hwnd = int(user32.GetForegroundWindow())

        if hwnd <= 0:
            raise RuntimeError(
                "No foreground window is available."
            )

        window_spec = desktop.window(handle=hwnd)
        return window_spec.wrapper_object()

    def perceive_structure_only(
        self,
        observation: EnvironmentObservation,
        *,
        max_descendants: int = 5_000,
        timeout_seconds: float = 2.0,
        diagnostic_callback: Callable[[dict[str, object]], None] | None = None,
        diagnostic_limit: int = 80,
    ) -> tuple[ScreenElement, ...]:
        """Observe table structure and optionally emit bounded, text-free diagnostics.

        Only the observed WindowHub form and its Windows-confirmed owned
        foreground popup are traversed. Diagnostic records contain UIA control
        type, class, AutomationId and bounded ancestor structure only. They
        never contain element/window text, values, headers or cell contents.
        """
        if (
            isinstance(max_descendants, bool)
            or not isinstance(max_descendants, int)
            or not 1 <= max_descendants <= 20_000
        ):
            raise ValueError("uia_structure_only_descendant_limit_invalid")
        if (
            isinstance(timeout_seconds, bool)
            or not isinstance(timeout_seconds, (int, float))
            or timeout_seconds <= 0
        ):
            raise ValueError("uia_structure_only_timeout_invalid")

        if (
            isinstance(diagnostic_limit, bool)
            or not isinstance(diagnostic_limit, int)
            or not 0 <= diagnostic_limit <= 500
        ):
            raise ValueError("uia_structure_only_diagnostic_limit_invalid")
        if diagnostic_callback is not None and not callable(diagnostic_callback):
            raise ValueError("uia_structure_only_diagnostic_callback_invalid")

        if self._desktop_factory is None and __import__("os").name != "nt":
            return ()

        main_handle = observation.metadata.get("window_handle")
        if (
            isinstance(main_handle, bool)
            or not isinstance(main_handle, int)
            or main_handle <= 0
        ):
            # Never fall back to whichever window happens to be foreground.
            return ()

        window_rect = observation.metadata.get("window_rect")
        origin_x = int(getattr(window_rect, "left", 0))
        origin_y = int(getattr(window_rect, "top", 0))

        foreground_handle = observation.metadata.get(
            "foreground_window_handle"
        )
        foreground_root_owner_handle = observation.metadata.get(
            "foreground_root_owner_handle"
        )
        window_root_owner_handle = observation.metadata.get(
            "window_root_owner_handle"
        )
        if (
            isinstance(window_root_owner_handle, bool)
            or not isinstance(window_root_owner_handle, int)
            or window_root_owner_handle <= 0
        ):
            # Backward-compatible observations created before root-owner
            # identity was captured. The live adapter supplies this value.
            window_root_owner_handle = main_handle

        # When a WindowHub-owned popup is foreground, scan it first. The
        # application root can contain a large MDI tree; scanning it first can
        # consume the whole deadline before the active lookup popup is inspected.
        # Both roots are still validated against the same Windows GA_ROOTOWNER.
        root_handles = []
        owned_foreground_popup = (
            isinstance(foreground_handle, int)
            and not isinstance(foreground_handle, bool)
            and foreground_handle > 0
            and foreground_handle != main_handle
            and foreground_root_owner_handle == window_root_owner_handle
        )
        if owned_foreground_popup:
            root_handles.append(foreground_handle)
        root_handles.append(main_handle)

        started_at = time.monotonic()
        elements: list[ScreenElement] = []
        seen_runtime_ids: set[str] = set()
        total_descendants = 0
        diagnostic_count = 0

        def emit_diagnostic(record: dict[str, object]) -> None:
            nonlocal diagnostic_count
            if diagnostic_callback is None or diagnostic_count >= diagnostic_limit:
                return
            diagnostic_type = record.get("diagnostic_type")
            is_lookup_edit = (
                str(record.get("automation_id", "")).casefold()
                == "idc_zamawiajacy"
                and str(record.get("class_name", "")).casefold()
                == "lookupedit"
            )
            is_priority = (
                diagnostic_type is not None
                or record.get("candidate_kind") == "table_control"
                or is_lookup_edit
            )
            # Reserve up to 16 entries for root lifecycle, Client LookupEdit,
            # and DataGrid candidates so a large MDI tree cannot crowd them out.
            reserved_records = min(16, max(1, diagnostic_limit // 4))
            normal_record_limit = max(0, diagnostic_limit - reserved_records)
            if not is_priority and diagnostic_count >= normal_record_limit:
                return
            diagnostic_count += 1
            try:
                diagnostic_callback(record)
            except Exception:
                # Diagnostics must never break the actual observation path.
                return

        try:
            desktop = (
                self._desktop_factory()
                if self._desktop_factory is not None
                else self._default_desktop()
            )
        except Exception as exc:
            emit_diagnostic({
                "diagnostic_type": "desktop_creation_failed",
                "error_type": type(exc).__name__,
            })
            return ()

        for root_handle in root_handles:
            elapsed = time.monotonic() - started_at
            if elapsed > timeout_seconds:
                emit_diagnostic({
                    "diagnostic_type": "root_scan_skipped",
                    "root_window_handle": root_handle,
                    "reason": "overall_timeout",
                    "elapsed_seconds": round(elapsed, 3),
                })
                return ()

            emit_diagnostic({
                "diagnostic_type": "root_scan_started",
                "root_window_handle": root_handle,
            })
            try:
                window = desktop.window(
                    handle=root_handle,
                ).wrapper_object()
            except Exception as exc:
                emit_diagnostic({
                    "diagnostic_type": "root_lookup_failed",
                    "root_window_handle": root_handle,
                    "error_type": type(exc).__name__,
                })
                continue

            try:
                descendants = window.descendants()
            except Exception as exc:
                emit_diagnostic({
                    "diagnostic_type": "root_descendants_failed",
                    "root_window_handle": root_handle,
                    "error_type": type(exc).__name__,
                })
                continue

            root_descendant_count = 0
            for item in descendants:
                total_descendants += 1
                root_descendant_count += 1
                if total_descendants > max_descendants:
                    emit_diagnostic({
                        "diagnostic_type": "scan_incomplete",
                        "root_window_handle": root_handle,
                        "reason": "max_descendants_exceeded",
                        "max_descendants": max_descendants,
                        "observed_descendants": total_descendants,
                    })
                    # Do not return a partial tree: a missing grid could make
                    # a false negative look like a complete observation.
                    return ()
                elapsed = time.monotonic() - started_at
                if elapsed > timeout_seconds:
                    emit_diagnostic({
                        "diagnostic_type": "scan_incomplete",
                        "root_window_handle": root_handle,
                        "reason": "overall_timeout",
                        "elapsed_seconds": round(elapsed, 3),
                        "observed_descendants": total_descendants,
                    })
                    return ()

                try:
                    info = item.element_info
                    control_type = self._normalize_control_type(
                        getattr(info, "control_type", None)
                    )
                    visible = bool(getattr(info, "visible", True))
                    automation_id = self._string(
                        getattr(info, "automation_id", None)
                    )
                    class_name = self._string(
                        getattr(info, "class_name", None)
                    )
                    runtime_id = self._runtime_id(item)
                    ancestor_structure = self._ancestor_structure(item)
                except Exception as exc:
                    emit_diagnostic({
                        "diagnostic_type": "node_metadata_failed",
                        "root_window_handle": root_handle,
                        "error_type": type(exc).__name__,
                    })
                    continue

                if control_type not in self.TABLE_CONTROL_TYPES:
                    if runtime_id:
                        emit_diagnostic({
                            "root_window_handle": root_handle,
                            "control_type": control_type,
                            "class_name": class_name or "",
                            "automation_id": automation_id or "",
                            "visible": visible,
                            "ancestor_structure": ancestor_structure,
                        })
                    continue

                # Table candidates receive a diagnostic record even when UIA
                # cannot provide usable bounds or a stable RuntimeId. This is
                # essential for distinguishing "not present" from "present
                # but not projectable into a ScreenElement".
                table_diagnostic = {
                    "root_window_handle": root_handle,
                    "control_type": control_type,
                    "class_name": class_name or "",
                    "automation_id": automation_id or "",
                    "visible": visible,
                    "ancestor_structure": ancestor_structure,
                    "candidate_kind": "table_control",
                }
                if not visible:
                    table_diagnostic["rejection_reason"] = "not_visible"
                    emit_diagnostic(table_diagnostic)
                    continue
                if not runtime_id:
                    table_diagnostic["rejection_reason"] = "runtime_id_unavailable"
                    emit_diagnostic(table_diagnostic)
                    continue
                if runtime_id in seen_runtime_ids:
                    table_diagnostic["rejection_reason"] = "duplicate_runtime_id"
                    emit_diagnostic(table_diagnostic)
                    continue

                try:
                    rectangle = item.rectangle()
                    rect = _UIARect(
                        left=int(rectangle.left) - origin_x,
                        top=int(rectangle.top) - origin_y,
                        width=int(rectangle.width()),
                        height=int(rectangle.height()),
                    )
                except Exception as exc:
                    table_diagnostic["rejection_reason"] = "rectangle_error"
                    table_diagnostic["rectangle_error_type"] = type(exc).__name__
                    emit_diagnostic(table_diagnostic)
                    continue

                table_diagnostic["bounds"] = (
                    rect.left,
                    rect.top,
                    rect.width,
                    rect.height,
                )
                if rect.width <= 0 or rect.height <= 0:
                    table_diagnostic["rejection_reason"] = "non_positive_bounds"
                    emit_diagnostic(table_diagnostic)
                    continue

                table_diagnostic["bounds_status"] = "usable"
                emit_diagnostic(table_diagnostic)
                seen_runtime_ids.add(runtime_id)
                element_id = f"uia:{runtime_id}"
                label = "Tabela"
                capability = InteractionCapability.NOT_INTERACTIVE
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
                            rect.left,
                            rect.top,
                            rect.width,
                            rect.height,
                        ),
                        confidence=0.99,
                        element_id=element_id,
                    ),
                )
                elements.append(
                    ScreenElement(
                        kind="table",
                        label=label,
                        x=rect.left,
                        y=rect.top,
                        width=rect.width,
                        height=rect.height,
                        confidence=0.99,
                        metadata={
                            "source": "windowhub_ui_automation",
                            "provider_element_id": element_id,
                            "semantic_name": label,
                            "semantic_label_source": "structure_only",
                            "uia_ancestor_structure": ancestor_structure,
                            "automation_id": automation_id,
                            "uia_class_name": class_name,
                            "uia_control_type": control_type,
                            "uia_visible": True,
                            "uia_runtime_id": runtime_id,
                            # Local-only identity used to re-resolve a popup
                            # in the next broker call; never sent to NaviMind.
                            "uia_root_window_handle": root_handle,
                            "interaction_capability": capability.value,
                            "interaction_capability_confidence": 0.99,
                            "perception_mode": "structure_only",
                        },
                        interaction_capability=capability,
                        evidence=evidence,
                    )
                )

            emit_diagnostic({
                "diagnostic_type": "root_scan_completed",
                "root_window_handle": root_handle,
                "descendant_count": root_descendant_count,
                "table_candidate_count": sum(
                    1 for element in elements
                    if (element.metadata or {}).get("uia_root_window_handle")
                    == root_handle
                ),
            })

        return tuple(elements)

    def resolve_table_element(
        self,
        target: ScreenElement,
        observation: EnvironmentObservation,
        *,
        required_ancestor_automation_ids: tuple[str, ...] = (),
        required_ancestor_properties: Mapping[str, str] | None = None,
    ):
        """Re-resolve one table target in the current window; never use a cached wrapper."""
        metadata = target.metadata or {}
        if target.kind != "table":
            raise ValueError("uia_table_target_kind_invalid")
        if metadata.get("source") != "windowhub_ui_automation":
            raise ValueError("uia_table_target_source_invalid")

        expected_runtime_id = metadata.get("uia_runtime_id")
        expected_automation_id = metadata.get("automation_id")
        expected_control_type = self._normalize_control_type(
            metadata.get("uia_control_type")
        )
        if (
            not isinstance(expected_runtime_id, str)
            or not expected_runtime_id.strip()
            or expected_control_type not in self.TABLE_CONTROL_TYPES
        ):
            raise ValueError("uia_table_target_identity_missing")
        if expected_automation_id is not None and (
            not isinstance(expected_automation_id, str)
            or not expected_automation_id.strip()
        ):
            raise ValueError("uia_table_target_automation_id_invalid")
        if not isinstance(required_ancestor_automation_ids, tuple) or any(
            not isinstance(value, str) or not value.strip()
            for value in required_ancestor_automation_ids
        ):
            raise ValueError("uia_table_required_ancestor_identity_invalid")
        if required_ancestor_properties is not None:
            allowed_parent_fields = {
                "control_type",
                "class_name",
                "automation_id",
            }
            if (
                not isinstance(required_ancestor_properties, Mapping)
                or not required_ancestor_properties
                or set(required_ancestor_properties) - allowed_parent_fields
                or any(
                    not isinstance(value, str) or not value.strip()
                    for value in required_ancestor_properties.values()
                )
            ):
                raise ValueError("uia_table_required_ancestor_properties_invalid")

        desktop = (
            self._desktop_factory()
            if self._desktop_factory is not None
            else self._default_desktop()
        )
        if metadata.get("perception_mode") == "structure_only":
            root_handle = metadata.get("uia_root_window_handle")
            main_handle = observation.metadata.get("window_handle")
            foreground_handle = observation.metadata.get(
                "foreground_window_handle"
            )
            foreground_owner = observation.metadata.get(
                "foreground_root_owner_handle"
            )
            app_root_owner = observation.metadata.get(
                "window_root_owner_handle"
            )
            if (
                isinstance(app_root_owner, bool)
                or not isinstance(app_root_owner, int)
                or app_root_owner <= 0
            ):
                app_root_owner = main_handle
            if (
                isinstance(root_handle, bool)
                or not isinstance(root_handle, int)
                or root_handle <= 0
                or isinstance(main_handle, bool)
                or not isinstance(main_handle, int)
                or main_handle <= 0
            ):
                raise ValueError("uia_structure_only_root_identity_invalid")
            if root_handle != main_handle and not (
                root_handle == foreground_handle
                and foreground_owner == app_root_owner
            ):
                raise RuntimeError("uia_structure_only_popup_owner_changed")
            window = desktop.window(
                handle=root_handle,
            ).wrapper_object()
        else:
            window = self._active_window(
                desktop,
                observation,
                allow_test_factory_fallback=(
                    self._desktop_factory is not None
                ),
            )

        expected_title = observation.state.active_window_title
        if (
            expected_title
            and metadata.get("perception_mode") != "structure_only"
            and window.window_text() != expected_title
        ):
            raise RuntimeError("uia_table_active_window_changed")

        matches = []
        for item in window.descendants():
            try:
                control_type = self._normalize_control_type(
                    getattr(item.element_info, "control_type", None)
                )
                runtime_id = self._runtime_id(item)
                automation_id = self._string(
                    getattr(item.element_info, "automation_id", None)
                )
                visible = bool(
                    getattr(item.element_info, "visible", True)
                )
            except Exception:
                continue

            if (
                visible
                and control_type == expected_control_type
                and runtime_id == expected_runtime_id
                and (
                    expected_automation_id is None
                    or (
                        isinstance(automation_id, str)
                        and automation_id.casefold()
                        == expected_automation_id.casefold()
                    )
                )
                and self._has_ancestor_automation_ids(
                    item,
                    required_ancestor_automation_ids,
                )
                and self._has_ancestor_properties(
                    item,
                    required_ancestor_properties,
                )
            ):
                matches.append(item)

        if len(matches) != 1:
            raise LookupError("uia_table_target_not_unique_or_not_found")
        return matches[0]

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
        label_candidates=(),
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

        if not visible:
            return None

        is_table = control_type in self.TABLE_CONTROL_TYPES
        if (
            control_type not in self.INTERACTIVE_CONTROL_TYPES
            and not is_table
        ):
            return None

        semantic_label, semantic_source = (
            self._resolve_semantic_label(
                item=item,
                name=name,
                control_type=control_type,
                rectangle=rectangle,
                origin_x=origin_x,
                origin_y=origin_y,
                label_candidates=label_candidates,
            )
        )

        # A nameless DataGrid is still a useful structural target. Keep its
        # label explicitly generic rather than borrowing an ambiguous label.
        if not semantic_label and is_table:
            semantic_label = "Tabela danych"
            semantic_source = "uia_control_type"

        if not semantic_label:
            return None

        rect = _UIARect(
            left=int(rectangle.left) - origin_x,
            top=int(rectangle.top) - origin_y,
            width=int(rectangle.width()),
            height=int(rectangle.height()),
        )

        if rect.width <= 0 or rect.height <= 0:
            return None

        # AutomationId is a runtime/provider identifier, not a semantic
        # display label. It remains available only in provider metadata.
        label = semantic_label
        capability = (
            InteractionCapability.NOT_INTERACTIVE
            if is_table or not enabled
            else InteractionCapability.CLICKABLE
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

        # Never ask a table/grid for its aggregate text here. Row values
        # are available only through an explicitly authorized observation.
        current_value = (
            None if is_table else self._current_control_value(item)
        )
        ancestor_context = self._ancestor_context(item)
        ancestor_structure = self._ancestor_structure(item)
        document_scope = self._document_scope(item)
        tab_scope = (
            self._tab_scope(item)
            if control_type == "tabitem"
            else None
        )
        # SelectionItemPattern is meaningful for document tabs and radio
        # buttons. Keyboard focus is reported separately and must never be
        # used as a substitute for the selected state.
        selected = (
            self._selection_state(item)
            if control_type == "radiobutton" or tab_scope == "document"
            else None
        )

        checked = (
            self._toggle_state(item)
            if control_type == "checkbox"
            else None
        )

        metadata = {
            "source": "windowhub_ui_automation",
            "provider_element_id": element_id,
            "semantic_name": label,
            "name": name,
            "semantic_label_source": semantic_source,
            "current_value": current_value,
            # Structural UIA context is observational evidence only. It is
            # deliberately not treated as a document scope by itself.
            "uia_ancestor_context": ancestor_context,
            # Provider-local structural identity; never a public model target.
            "uia_ancestor_structure": ancestor_structure,
            "document_scope": document_scope,
            "automation_id": automation_id,
            "uia_control_type": control_type,
            "uia_enabled": enabled,
            "uia_visible": visible,
            "uia_runtime_id": runtime_id,
            "uia_selected": selected,
            "uia_checked": checked,
            "uia_focused": self._keyboard_focus_state(item),
            "uia_tab_scope": tab_scope,
            "uia_document_tab_selected": (
                selected
                if tab_scope == "document"
                else None
            ),
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
            kind="table" if is_table else control_type,
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
    def _ancestor_context(
        item,
        *,
        max_depth: int = 8,
    ) -> tuple[tuple[str | None, str | None, str | None], ...]:
        """
        Capture a bounded semantic UIA ancestry path.

        This is observational context for reasoning, diagnostics and later
        scope inference. It must not by itself authorize a document scope,
        because WindowHub's document content may not be a direct child of
        its document tab control.
        """
        context = []
        current = item

        for _ in range(max_depth):
            parent_getter = getattr(current, "parent", None)
            if not callable(parent_getter):
                break

            try:
                current = parent_getter()
            except Exception:
                break

            if current is None:
                break

            try:
                element_info = current.element_info
                control_type = WindowHubUIAutomationProvider._string(
                    getattr(element_info, "control_type", None)
                )
                class_name = WindowHubUIAutomationProvider._string(
                    getattr(element_info, "class_name", None)
                )
                name = WindowHubUIAutomationProvider._string(
                    getattr(element_info, "name", None)
                )
            except Exception:
                break

            context.append(
                (
                    control_type,
                    class_name,
                    name,
                )
            )

        return tuple(context)

    @staticmethod
    def _ancestor_structure(
        item,
        *,
        max_depth: int = 8,
    ) -> tuple[dict[str, str | None], ...]:
        """Capture stable UIA parent properties without reading text or values."""
        structure = []
        current = item

        for _ in range(max_depth):
            parent_getter = getattr(current, "parent", None)
            if not callable(parent_getter):
                break
            try:
                current = parent_getter()
            except Exception:
                break
            if current is None:
                break

            try:
                info = current.element_info
                structure.append(
                    {
                        "control_type": (
                            WindowHubUIAutomationProvider._string(
                                getattr(info, "control_type", None)
                            ) or ""
                        ).casefold(),
                        "class_name": (
                            WindowHubUIAutomationProvider._string(
                                getattr(info, "class_name", None)
                            ) or ""
                        ).casefold(),
                        "automation_id": (
                            WindowHubUIAutomationProvider._string(
                                getattr(info, "automation_id", None)
                            ) or ""
                        ).casefold(),
                    }
                )
            except Exception:
                break

        return tuple(structure)

    @classmethod
    def _has_ancestor_automation_ids(
        cls,
        item,
        required_ids: tuple[str, ...],
    ) -> bool:
        if not required_ids:
            return True
        actual_ids = {
            entry["automation_id"].casefold()
            for entry in cls._ancestor_structure(item)
            if entry.get("automation_id")
        }
        return all(value.casefold() in actual_ids for value in required_ids)

    @classmethod
    def _has_ancestor_properties(
        cls,
        item,
        required_properties: Mapping[str, str] | None,
    ) -> bool:
        """Require all supplied properties to match the same UIA ancestor."""
        if required_properties is None:
            return True

        expected = {
            key: value.strip().casefold()
            for key, value in required_properties.items()
        }
        for ancestor in cls._ancestor_structure(item):
            if all(
                ancestor.get(key, "").casefold() == value
                for key, value in expected.items()
            ):
                return True
        return False

    @staticmethod
    def _document_scope(item) -> str | None:
        """
        Return a document tab name only when UIA proves that the element
        is structurally contained by a WindowHub document tab.

        This is intentionally narrower than generic ancestor inspection:
        the candidate tab must itself be a TabItem whose parent is the
        WindowHub Afx:TabWnd host. If that relationship is absent, scope
        remains unknown.
        """
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
                element_info = current.element_info
                control_type = str(
                    getattr(element_info, "control_type", "")
                ).strip().casefold()
                name = WindowHubUIAutomationProvider._string(
                    getattr(element_info, "name", None)
                )
            except Exception:
                return None

            if control_type != "tabitem" or not name:
                continue

            try:
                host = current.parent()
                host_info = host.element_info
                host_control_type = str(
                    getattr(host_info, "control_type", "")
                ).strip().casefold()
                host_class_name = str(
                    getattr(host_info, "class_name", "")
                ).strip().casefold()
            except Exception:
                continue

            if (
                host_control_type == "tab"
                and "afxtabwnd" in host_class_name.replace(":", "")
            ):
                return name

        return None

    @staticmethod
    def _tab_scope(item) -> str | None:
        """
        Distinguish WindowHub document tabs from nested tabs such as
        the per-document "Notatka" tab.

        WindowHub exposes document tabs under an MDI tab host with the
        "Afx:TabWnd" class, while nested tabs use standard SysTabControl32.
        """
        try:
            parent = item.parent()
        except Exception:
            return None

        if parent is None:
            return None

        try:
            control_type = str(
                getattr(
                    parent.element_info,
                    "control_type",
                    "",
                )
            ).strip().casefold()
            class_name = str(
                getattr(
                    parent.element_info,
                    "class_name",
                    "",
                )
            ).strip().casefold()
        except Exception:
            return None

        if control_type != "tab":
            return None

        if "afxtabwnd" in class_name.replace(":", ""):
            return "document"

        if "systabcontrol32" in class_name:
            return "nested"

        return "other"

    @staticmethod
    def _keyboard_focus_state(item) -> bool | None:
        """Read UIA keyboard focus when the provider exposes it."""
        try:
            element_info = item.element_info
        except Exception:
            element_info = None

        for owner in (element_info, item):
            if owner is None:
                continue
            try:
                value = getattr(owner, "has_keyboard_focus", None)
                if callable(value):
                    value = value()
                if isinstance(value, bool):
                    return value
            except Exception:
                continue

        properties_getter = getattr(item, "get_properties", None)
        if callable(properties_getter):
            try:
                properties = properties_getter()
            except Exception:
                properties = {}
            if isinstance(properties, dict):
                for key in (
                    "has_keyboard_focus",
                    "keyboard_focus",
                    "focused",
                ):
                    value = properties.get(key)
                    if isinstance(value, bool):
                        return value
        return None

    @staticmethod
    def _selection_state(item) -> bool | None:
        """
        Read SelectionItemPattern state for selectable UIA controls.

        WindowHub exposes document tabs and radio-button options through
        UIA selection-item controls. The selection state is observed from
        SelectionItemPattern rather than inferred from keyboard focus,
        position, styling, or window title.
        """
        try:
            iface = getattr(item, "iface_selection_item", None)
            if iface is not None:
                return bool(iface.CurrentIsSelected)
        except Exception:
            pass

        try:
            properties = item.get_properties()
        except Exception:
            properties = {}

        if isinstance(properties, dict):
            for key in (
                "is_selected",
                "selection_item_is_selected",
                "selected",
            ):
                value = properties.get(key)
                if isinstance(value, bool):
                    return value

        return None

    @staticmethod
    def _toggle_state(item) -> bool | None:
        """Read UIA TogglePattern state; unknown/indeterminate is never False."""
        try:
            iface = getattr(item, "iface_toggle", None)
            state = getattr(iface, "CurrentToggleState", None) if iface is not None else None
            if state is not None and not isinstance(state, bool):
                value = int(state)
                if value in (0, 1):
                    return value == 1
        except Exception:
            pass

        try:
            properties = item.get_properties()
        except Exception:
            properties = {}
        if isinstance(properties, dict):
            for key in ("toggle_state", "checked", "is_checked"):
                value = properties.get(key)
                if isinstance(value, bool):
                    return value
                if isinstance(value, int) and value in (0, 1):
                    return value == 1
        return None

    @staticmethod
    def _current_control_value(item) -> str | None:
        for method_name in (
            "get_value",
            "window_text",
        ):
            method = getattr(item, method_name, None)
            if not callable(method):
                continue

            try:
                value = method()
            except Exception:
                continue

            if isinstance(value, str):
                value = value.strip()
                if value:
                    return value

        element_info = getattr(
            item,
            "element_info",
            None,
        )

        for attribute_name in (
            "value",
            "legacy_value",
            "rich_text",
        ):
            value = getattr(
                element_info,
                attribute_name,
                None,
            )
            if isinstance(value, str) and value.strip():
                return value.strip()

        return None

    @classmethod
    def _collect_label_candidates(
        cls,
        items,
        origin_x: int,
        origin_y: int,
    ):
        candidates = []

        for item in items:
            try:
                element_info = item.element_info
                control_type = cls._normalize_control_type(
                    getattr(element_info, "control_type", None)
                )
                visible = bool(
                    getattr(element_info, "visible", True)
                )
                if not visible:
                    continue

                if control_type not in {
                    "text",
                    "label",
                }:
                    continue

                label = cls._best_text_value(item)
                if not label or cls._is_generic_label(label):
                    continue

                rectangle = item.rectangle()
                rect = _UIARect(
                    left=int(rectangle.left) - origin_x,
                    top=int(rectangle.top) - origin_y,
                    width=int(rectangle.width()),
                    height=int(rectangle.height()),
                )

                if rect.width <= 0 or rect.height <= 0:
                    continue

                candidates.append(
                    (
                        rect,
                        label,
                        "uia_text_neighbor",
                    )
                )
            except Exception:
                continue

        return tuple(candidates)

    @classmethod
    def _resolve_semantic_label(
        cls,
        *,
        item,
        name: str | None,
        control_type: str,
        rectangle,
        origin_x: int,
        origin_y: int,
        label_candidates,
    ) -> tuple[str | None, str]:
        if name and not cls._is_generic_label(name):
            return name, "uia_name"

        parent_label = cls._parent_semantic_label(item)
        if parent_label:
            return parent_label, "uia_parent"

        rect = _UIARect(
            left=int(rectangle.left) - origin_x,
            top=int(rectangle.top) - origin_y,
            width=int(rectangle.width()),
            height=int(rectangle.height()),
        )

        nearby = []
        for label_rect, label, source in label_candidates:
            score = cls._label_proximity_score(
                control_rect=rect,
                label_rect=label_rect,
            )
            if score is not None:
                nearby.append(
                    (
                        score,
                        label,
                        source,
                    )
                )

        if not nearby:
            return None, "none"

        nearby.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        best = nearby[0]

        if len(nearby) > 1:
            margin = best[0] - nearby[1][0]
            if margin < 0.08:
                return None, "ambiguous_neighbor"

        return best[1], best[2]

    @classmethod
    def _parent_semantic_label(
        cls,
        item,
    ) -> str | None:
        parent_getter = getattr(item, "parent", None)
        if not callable(parent_getter):
            return None

        current = item

        for _ in range(5):
            try:
                current = current.parent()
            except Exception:
                return None

            if current is None:
                return None

            label = cls._best_text_value(current)
            if label and not cls._is_generic_label(label):
                return label

        return None

    @classmethod
    def _best_text_value(
        cls,
        item,
    ) -> str | None:
        element_info = getattr(item, "element_info", None)

        for source in (
            getattr(element_info, "name", None),
            getattr(element_info, "rich_text", None),
            getattr(element_info, "help_text", None),
            getattr(element_info, "item_status", None),
            getattr(item, "window_text", None),
        ):
            value = source() if callable(source) else source
            if isinstance(value, str):
                value = value.strip()
                if value:
                    return value

        get_properties = getattr(
            item,
            "get_properties",
            None,
        )
        if callable(get_properties):
            try:
                properties = get_properties()
            except Exception:
                properties = {}

            if isinstance(properties, dict):
                for key in (
                    "name",
                    "rich_text",
                    "help_text",
                    "item_status",
                ):
                    value = properties.get(key)
                    if isinstance(value, str) and value.strip():
                        return value.strip()

        return None

    @staticmethod
    def _is_generic_label(value: str) -> bool:
        normalized = value.strip().casefold()

        return normalized in {
            "",
            "layoutitem",
            "comboboxedit",
            "dateedit",
            "textbox",
            "edit",
            "control",
        }

    @staticmethod
    def _label_proximity_score(
        *,
        control_rect: _UIARect,
        label_rect: _UIARect,
    ) -> float | None:
        control_center = control_rect.center
        label_center = label_rect.center

        left_gap = control_rect.left - label_rect.right
        vertical_overlap = min(
            control_rect.bottom,
            label_rect.bottom,
        ) - max(
            control_rect.top,
            label_rect.top,
        )

        if 0 <= left_gap <= 260 and vertical_overlap > 0:
            vertical_distance = abs(
                control_center[1] - label_center[1]
            )
            return max(
                0.0,
                1.0
                - (
                    left_gap / 260.0
                )
                - min(
                    vertical_distance / 240.0,
                    0.35,
                ),
            )

        top_gap = control_rect.top - label_rect.bottom
        horizontal_overlap = min(
            control_rect.right,
            label_rect.right,
        ) - max(
            control_rect.left,
            label_rect.left,
        )

        if 0 <= top_gap <= 100 and horizontal_overlap > 0:
            horizontal_distance = abs(
                control_center[0] - label_center[0]
            )
            return max(
                0.0,
                0.82
                - (
                    top_gap / 100.0
                )
                - min(
                    horizontal_distance / 300.0,
                    0.35,
                ),
            )

        return None

    @staticmethod
    def _correlate_tracked_object(
        rect: _UIARect,
        tracked_objects,
    ) -> str | None:
        candidates = []

        for tracked in tracked_objects:
            status = getattr(tracked, "status", None)
            if getattr(status, "value", status) == "lost":
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
