from __future__ import annotations

from dataclasses import dataclass
import unicodedata
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

    MAX_GRID_CELLS_PER_GRID = 1000

    def __init__(
        self,
        *,
        desktop_factory: Callable[[], object] | None = None,
        pattern_interface_getter: Callable[[object, str], object] | None = None,
    ) -> None:
        self._desktop_factory = desktop_factory
        self._pattern_interface_getter = pattern_interface_getter

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
                actual_title = window.window_text()
                if (
                    actual_title.strip()
                    != expected_title.strip()
                ):
                    return ()
            except Exception:
                return ()

        window_rect = observation.metadata.get("window_rect")
        origin_x = int(getattr(window_rect, "left", 0))
        origin_y = int(getattr(window_rect, "top", 0))

        tracked_objects = self._tracked_objects(observation)
        windows = [window]

        root_handle = observation.metadata.get("window_handle")
        foreground_handle = observation.metadata.get(
            "foreground_window_handle"
        )
        foreground_owner = observation.metadata.get(
            "foreground_root_owner_handle"
        )

        try:
            root_handle_int = int(root_handle or 0)
            foreground_handle_int = int(foreground_handle or 0)
            foreground_owner_int = int(foreground_owner or 0)
        except (TypeError, ValueError):
            root_handle_int = 0
            foreground_handle_int = 0
            foreground_owner_int = 0

        # A modal/owned WindowHub dialog is a separate top-level window.
        # Perceive it alongside the main WindowHub root so controls such as
        # "Dalej >" become part of the current semantic scene.
        if (
            foreground_handle_int > 0
            and foreground_handle_int != root_handle_int
            and foreground_owner_int == root_handle_int
        ):
            try:
                dialog_spec = desktop.window(
                    handle=foreground_handle_int
                )
                wrapper = getattr(dialog_spec, "wrapper_object", None)
                dialog = (
                    wrapper()
                    if callable(wrapper)
                    else dialog_spec
                )
                windows.append(dialog)
            except Exception:
                pass

        elements: list[ScreenElement] = []

        for window_index, current_window in enumerate(windows):
            try:
                descendants = tuple(current_window.descendants())
            except Exception:
                continue

            is_owned_modal = (
                window_index > 0
                and foreground_handle_int > 0
                and foreground_owner_int == root_handle_int
            )
            current_window_handle = (
                foreground_handle_int
                if is_owned_modal
                else root_handle_int
            )

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
                    window_handle=current_window_handle,
                    owned_modal=is_owned_modal,
                )
                if element is not None:
                    elements.append(element)

            # Grid cells are often exposed by WindowHub as custom controls,
            # and their UIA Visible property may be unreliable. Read cells
            # through GridPattern only after a unique MDI document/tab match.
            elements.extend(
                self._collect_grid_cells(
                    descendants=descendants,
                    origin_x=origin_x,
                    origin_y=origin_y,
                    window_handle=current_window_handle,
                    owned_modal=is_owned_modal,
                )
            )

        return tuple(elements)

    def _collect_grid_cells(
        self,
        *,
        descendants,
        origin_x: int,
        origin_y: int,
        window_handle: int,
        owned_modal: bool,
    ) -> tuple[ScreenElement, ...]:
        """Emit read-only GridPattern cell observations with proven MDI scope."""
        matched_documents = self._matched_mdi_document_windows(descendants)
        if not matched_documents:
            return ()

        elements: list[ScreenElement] = []
        for document_index, (
            document_key,
            document_scope,
            child_window,
        ) in enumerate(matched_documents):
            try:
                document_descendants = tuple(child_window.descendants())
            except Exception:
                continue

            grids = []
            for item in document_descendants:
                try:
                    info = item.element_info
                    control_type = self._normalize_control_type(
                        getattr(info, "control_type", None)
                    )
                except Exception:
                    continue
                if control_type in {"datagrid", "table"}:
                    grids.append(item)

            for grid_index, grid in enumerate(grids):
                try:
                    grid_iface = getattr(grid, "iface_grid")
                    row_count = int(grid_iface.CurrentRowCount)
                    column_count = int(grid_iface.CurrentColumnCount)
                    rectangle = grid.rectangle()
                    grid_rect = _UIARect(
                        left=int(rectangle.left),
                        top=int(rectangle.top),
                        width=int(rectangle.width()),
                        height=int(rectangle.height()),
                    )
                except Exception:
                    continue

                if (
                    row_count <= 0
                    or column_count <= 0
                    or grid_rect.width <= 0
                    or grid_rect.height <= 0
                ):
                    continue

                total_cells = row_count * column_count
                cells_to_read = min(
                    total_cells,
                    self.MAX_GRID_CELLS_PER_GRID,
                )
                grid_runtime_id = self._runtime_id(grid)
                grid_identity = (
                    f"doc{document_index}:{document_key}:"
                    f"{grid_runtime_id or self._native_handle(grid) or 'grid'}:"
                    f"grid{grid_index}"
                )
                enumeration_truncated = total_cells > cells_to_read

                for cell_index in range(cells_to_read):
                    row = cell_index // column_count
                    column = cell_index % column_count

                    try:
                        cell = grid_iface.GetItem(row, column)
                    except Exception:
                        continue

                    if cell is None:
                        continue

                    offscreen = self._uia_cell_offscreen(cell)
                    if offscreen is True:
                        continue

                    cell_rect = self._uia_element_bounds(cell)
                    if cell_rect is None:
                        continue

                    # Reject cells outside the visible grid viewport. Some
                    # WPF wrappers report Visible=False for realized cells,
                    # so native UIA offscreen state plus bounds are used here.
                    if not self._rectangles_intersect(cell_rect, grid_rect):
                        continue

                    legacy = self._get_grid_pattern(cell, "LegacyIAccessible")
                    cell_label = self._pattern_string(legacy, "CurrentName")
                    if not cell_label:
                        cell_label = self._pattern_string(cell, "CurrentName")
                    if not cell_label:
                        continue

                    current_value = None
                    value_available = False
                    value_source = None

                    legacy_value = self._pattern_string_value(
                        legacy,
                        "CurrentValue",
                    )
                    if legacy_value[0]:
                        value_available = True
                        current_value = legacy_value[1]
                        value_source = "uia_legacy_accessible"
                    else:
                        value_pattern = self._get_grid_pattern(cell, "Value")
                        value_value = self._pattern_string_value(
                            value_pattern,
                            "CurrentValue",
                        )
                        if value_value[0]:
                            value_available = True
                            current_value = value_value[1]
                            value_source = "uia_value_pattern"

                    left = cell_rect.left - origin_x
                    top = cell_rect.top - origin_y
                    width = cell_rect.width
                    height = cell_rect.height
                    element_id = (
                        f"uia:gridcell:{grid_identity}:{row}:{column}"
                    )

                    evidence = [
                        SemanticEvidence(
                            source=EvidenceSource.ACCESSIBILITY,
                            kind=EvidenceKind.LABEL,
                            value=cell_label,
                            confidence=0.99,
                            element_id=element_id,
                        ),
                        SemanticEvidence(
                            source=EvidenceSource.ACCESSIBILITY,
                            kind=EvidenceKind.ROLE,
                            value="gridcell",
                            confidence=0.99,
                            element_id=element_id,
                        ),
                        SemanticEvidence(
                            source=EvidenceSource.ACCESSIBILITY,
                            kind=EvidenceKind.BOUNDS,
                            value=(left, top, width, height),
                            confidence=0.99,
                            element_id=element_id,
                        ),
                    ]
                    if value_available:
                        evidence.append(
                            SemanticEvidence(
                                source=EvidenceSource.ACCESSIBILITY,
                                kind=EvidenceKind.TEXT,
                                value=current_value,
                                confidence=0.99,
                                element_id=element_id,
                            )
                        )

                    grid_metadata = {
                        "source": "windowhub_ui_automation",
                        "provider_element_id": element_id,
                        "semantic_name": cell_label,
                        "name": cell_label,
                        "semantic_label_source": "uia_legacy_accessible_name",
                        "current_value": current_value,
                        "current_value_available": value_available,
                        "current_value_source": value_source,
                        "document_scope": document_scope,
                        "uia_control_type": "custom",
                        "uia_class_name": self._pattern_string(
                            cell,
                            "CurrentClassName",
                        ),
                        "uia_grid_cell_observation": True,
                        "uia_grid_id": grid_identity,
                        "uia_grid_index": grid_index,
                        "uia_grid_row_index": row,
                        "uia_grid_column_index": column,
                        "uia_grid_row_count": row_count,
                        "uia_grid_column_count": column_count,
                        "uia_grid_index_base": 0,
                        "uia_grid_enumeration_truncated": enumeration_truncated,
                        "uia_cell_offscreen": offscreen,
                        "uia_window_handle": window_handle,
                        "uia_owned_modal": owned_modal,
                        "interaction_capability": (
                            InteractionCapability.UNKNOWN.value
                        ),
                        "interaction_capability_confidence": 0.0,
                        "semantic_evidence": tuple(evidence),
                    }

                    elements.append(
                        ScreenElement(
                            kind="gridcell",
                            label=cell_label,
                            x=left,
                            y=top,
                            width=width,
                            height=height,
                            confidence=0.99,
                            metadata=grid_metadata,
                            interaction_capability=InteractionCapability.UNKNOWN,
                            evidence=tuple(evidence),
                        )
                    )

        return tuple(elements)

    @classmethod
    def _matched_mdi_document_windows(cls, descendants):
        """Match document tab captions to unique MDI child windows."""
        tabs_by_key: dict[str, list[str]] = {}
        windows_by_key: dict[str, list[object]] = {}

        for item in descendants:
            try:
                info = item.element_info
                control_type = cls._normalize_control_type(
                    getattr(info, "control_type", None)
                )
                name = cls._string(getattr(info, "name", None))
            except Exception:
                continue

            if not name:
                continue

            key = cls._normalized_document_key(name)
            if not key:
                continue

            if (
                control_type == "tabitem"
                and cls._tab_scope(item) == "document"
            ):
                tab_host = cls._grid_parent_item(item)
                mdi_client = (
                    cls._grid_parent_item(tab_host)
                    if tab_host is not None
                    else None
                )
                try:
                    host_info = (
                        tab_host.element_info
                        if tab_host is not None
                        else None
                    )
                    mdi_info = (
                        mdi_client.element_info
                        if mdi_client is not None
                        else None
                    )
                    is_expected_host = (
                        cls._normalize_control_type(
                            getattr(host_info, "control_type", None)
                        ) == "tab"
                        and "afxtabwnd" in (
                            cls._string(
                                getattr(host_info, "class_name", None)
                            ) or ""
                        ).replace(":", "").casefold()
                    )
                    is_expected_mdi = (
                        cls._normalize_control_type(
                            getattr(mdi_info, "control_type", None)
                        ) == "pane"
                        and (
                            cls._string(
                                getattr(mdi_info, "class_name", None)
                            ) or ""
                        ).casefold() == "mdiclient"
                    )
                except Exception:
                    is_expected_host = False
                    is_expected_mdi = False

                if is_expected_host and is_expected_mdi:
                    tabs_by_key.setdefault(key, []).append(name)
                continue

            if (
                control_type == "window"
                and cls._grid_parent_is_mdi_client(item)
            ):
                windows_by_key.setdefault(key, []).append(item)

        matched = []
        for key, tab_names in tabs_by_key.items():
            windows = windows_by_key.get(key, [])
            if len(tab_names) == 1 and len(windows) == 1:
                matched.append((key, tab_names[0], windows[0]))
        return tuple(matched)

    @classmethod
    def _grid_parent_item(cls, item):
        if item is None:
            return None
        try:
            getter = getattr(item, "parent", None)
            return getter() if callable(getter) else None
        except Exception:
            return None

    @classmethod
    def _grid_parent_is_mdi_client(cls, item) -> bool:
        parent = cls._grid_parent_item(item)
        if parent is None:
            return False
        try:
            info = parent.element_info
            return (
                cls._normalize_control_type(
                    getattr(info, "control_type", None)
                ) == "pane"
                and (
                    cls._string(getattr(info, "class_name", None)) or ""
                ).casefold() == "mdiclient"
            )
        except Exception:
            return False

    @staticmethod
    def _normalized_document_key(value: str) -> str:
        normalized = unicodedata.normalize("NFKC", value).casefold()
        return "".join(
            character
            for character in normalized
            if character.isalnum()
        )

    def _get_grid_pattern(self, cell, pattern_name):
        getter = self._pattern_interface_getter
        if getter is not None:
            try:
                return getter(cell, pattern_name)
            except Exception:
                return None

        try:
            from pywinauto.windows.uia_defines import get_elem_interface
        except ModuleNotFoundError:
            try:
                from pywinauto.uia_defines import get_elem_interface
            except Exception:
                return None
        except Exception:
            return None

        try:
            return get_elem_interface(cell, pattern_name)
        except Exception:
            return None

    @staticmethod
    def _pattern_string(pattern, property_name):
        if pattern is None:
            return None
        try:
            value = getattr(pattern, property_name)
        except Exception:
            return None
        return value.strip() if isinstance(value, str) and value.strip() else None

    @staticmethod
    def _pattern_string_value(pattern, property_name):
        if pattern is None:
            return False, None
        try:
            value = getattr(pattern, property_name)
        except Exception:
            return False, None
        if isinstance(value, str):
            # Preserve an observed empty string: blank cell is different from
            # a value that the provider could not read.
            return True, value
        return False, None

    @staticmethod
    def _uia_cell_offscreen(cell):
        try:
            value = getattr(cell, "CurrentIsOffscreen")
        except Exception:
            return None
        return bool(value) if value is not None else None

    @staticmethod
    def _uia_element_bounds(cell):
        try:
            raw = getattr(cell, "CurrentBoundingRectangle")
            left = int(raw.left)
            top = int(raw.top)
            right = int(raw.right)
            bottom = int(raw.bottom)
        except Exception:
            return None

        width = right - left
        height = bottom - top
        if width <= 0 or height <= 0:
            return None
        return _UIARect(left=left, top=top, width=width, height=height)

    @staticmethod
    def _rectangles_intersect(left: _UIARect, right: _UIARect) -> bool:
        return (
            left.left < right.right
            and right.left < left.right
            and left.top < right.bottom
            and right.top < left.bottom
        )

    @staticmethod
    def _default_desktop():
        from app.agent.platform.windows_com import ensure_windows_sta
        ensure_windows_sta()

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
            wrapper = getattr(window_spec, "wrapper_object", None)
            return (
                wrapper()
                if callable(wrapper)
                else window_spec
            )

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
        window_handle: int = 0,
        owned_modal: bool = False,
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

        if control_type not in self.INTERACTIVE_CONTROL_TYPES:
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

        current_value = self._current_control_value(item)
        ancestor_context = self._ancestor_context(item)
        document_scope = self._document_scope(item)
        tab_scope = (
            self._tab_scope(item)
            if control_type == "tabitem"
            else None
        )
        selected = (
            self._selection_state(item)
            if (
                control_type in {
                    "radiobutton",
                    "listitem",
                    "tabitem",
                    "treeitem",
                }
                or tab_scope == "document"
            )
            else None
        )

        focused = self._keyboard_focus_state(item)

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
            "document_scope": document_scope,
            "automation_id": automation_id,
            "uia_control_type": control_type,
            "uia_enabled": enabled,
            "uia_visible": visible,
            "uia_runtime_id": runtime_id,
            "uia_selected": selected,
            "uia_focused": focused,
            "uia_tab_scope": tab_scope,
            "uia_document_tab_selected": (
                selected
                if tab_scope == "document"
                else None
            ),
            # Enumeration context and the native HWND of the control are
            # distinct. Keep both so diagnostics can validate actual Win32
            # ownership instead of assuming every descendant belongs to root.
            "uia_window_handle": window_handle,
            "uia_native_handle": self._native_handle(item),
            "uia_owned_modal": owned_modal,
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
    def _ancestor_context(
        item,
        *,
        max_depth: int = 8,
    ) -> tuple[tuple[str | None, str | None, str | None, int | None], ...]:
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

            # Preserve the native handle separately from the descriptive
            # ancestry. The consumer may compare identities privately, but
            # should not treat ancestry alone as document ownership.
            context.append(
                (
                    control_type,
                    class_name,
                    name,
                    WindowHubUIAutomationProvider._native_handle(current),
                )
            )

        return tuple(context)

    @staticmethod
    def _native_handle(item) -> int | None:
        """Return the native HWND for this UIA element when exposed by pywinauto."""
        try:
            element_info = getattr(item, "element_info", None)
            raw_handle = getattr(element_info, "handle", None)
            if raw_handle is None:
                raw_handle = getattr(item, "handle", None)
                if callable(raw_handle):
                    raw_handle = raw_handle()
            handle = int(raw_handle)
        except (AttributeError, TypeError, ValueError, OSError):
            return None
        except Exception:
            return None

        return handle if handle > 0 else None

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
        """
        Read keyboard focus from UIA when the provider exposes it.

        Focus is observational context for semantic teaching only; it is
        never used as a persisted runtime identifier.
        """
        method = getattr(item, "has_keyboard_focus", None)
        if callable(method):
            try:
                return bool(method())
            except Exception:
                pass

        element_info = getattr(item, "element_info", None)

        for attribute_name in (
            "has_keyboard_focus",
            "keyboard_focus",
        ):
            value = getattr(
                element_info,
                attribute_name,
                None,
            )
            if isinstance(value, bool):
                return value

        try:
            properties = item.get_properties()
        except Exception:
            properties = {}

        if isinstance(properties, dict):
            for key in (
                "has_keyboard_focus",
                "keyboard_focus",
                "is_keyboard_focused",
            ):
                value = properties.get(key)
                if isinstance(value, bool):
                    return value

        return None

    @staticmethod
    def _selection_state(item) -> bool | None:
        """
        Read SelectionItemPattern state for selectable UIA controls.

        WindowHub exposes document tabs through TabItem controls. The
        selection state is observed from UIA rather than inferred from
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
