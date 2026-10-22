from __future__ import annotations

import ctypes
import os
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


class _RECT(ctypes.Structure):
    _fields_ = (
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    )


class _POINT(ctypes.Structure):
    _fields_ = (
        ("x", ctypes.c_long),
        ("y", ctypes.c_long),
    )


class WindowHubWin32FormProvider(PerceptionProvider):
    """Read-only native Win32 fallback for fields missing from WindowHub UIA.

    The provider emits only controls whose HWND ancestry is inside one
    uniquely resolved native child window whose title exactly matches the
    uniquely selected UIA document tab. Each emitted control must also have
    one unambiguous, nearby native static-text label in the same native
    container. Geometry and label proximity are evidence for candidate
    association, not independent proof of document scope.

    The provider never invokes controls or changes their contents.
    """

    FIELD_CLASS_TO_KIND = {
        "edit": "edit",
        "combobox": "combobox",
    }
    LABEL_CLASSES = frozenset({"static", "text"})

    def __init__(
        self,
        *,
        document_label_resolver: Callable[
            [EnvironmentObservation, int], str | None
        ] | None = None,
        native_snapshot_factory: Callable[
            [int], tuple[dict[str, object], ...] | list[dict[str, object]] | None
        ] | None = None,
    ) -> None:
        # Injection points keep the correlation policy testable off Windows.
        self._document_label_resolver = (
            document_label_resolver
            if document_label_resolver is not None
            else self._resolve_selected_document_label
        )
        self._native_snapshot_factory = (
            native_snapshot_factory
            if native_snapshot_factory is not None
            else self._snapshot_native_windows
        )

    def perceive(
        self,
        observation: EnvironmentObservation,
    ) -> tuple[ScreenElement, ...]:
        if os.name != "nt" and (
            self._document_label_resolver == self._resolve_selected_document_label
            or self._native_snapshot_factory == self._snapshot_native_windows
        ):
            return ()

        metadata = observation.metadata or {}
        root_handle = self._positive_handle(metadata.get("window_handle"))
        if root_handle is None:
            return ()

        title = observation.state.active_window_title
        if not isinstance(title, str) or not title.strip():
            return ()
        if not title.strip().casefold().startswith("okna -"):
            return ()

        root_rect = metadata.get("window_rect")
        try:
            root_left = int(getattr(root_rect, "left"))
            root_top = int(getattr(root_rect, "top"))
        except (TypeError, ValueError, AttributeError, OverflowError):
            return ()

        try:
            document_label = self._document_label_resolver(
                observation,
                root_handle,
            )
        except Exception:
            return ()
        if not isinstance(document_label, str) or not document_label.strip():
            return ()
        document_label = document_label.strip()

        try:
            records = self._native_snapshot_factory(root_handle)
        except Exception:
            return ()
        if records is None:
            return ()

        return self._elements_from_snapshot(
            tuple(records),
            root_handle=root_handle,
            root_left=root_left,
            root_top=root_top,
            document_label=document_label,
        )

    @classmethod
    def _elements_from_snapshot(
        cls,
        records: tuple[dict[str, object], ...],
        *,
        root_handle: int,
        root_left: int,
        root_top: int,
        document_label: str,
    ) -> tuple[ScreenElement, ...]:
        """Build fields from a native snapshot, rejecting ambiguous scope."""
        document_candidates = [
            record
            for record in records
            if (
                cls._normalized_text(record.get("title"))
                == cls._normalized_text(document_label)
                and record.get("visible") is True
                and root_handle in cls._handle_chain(record.get("parent_chain"))
                and cls._positive_handle(record.get("handle")) is not None
                and cls._valid_bounds(record.get("client_bounds")) is not None
            )
        ]
        # Never guess between similarly named child windows.
        if len(document_candidates) != 1:
            return ()

        document = document_candidates[0]
        document_handle = cls._positive_handle(document.get("handle"))
        document_bounds = cls._valid_bounds(document.get("client_bounds"))
        if document_handle is None or document_bounds is None:
            return ()

        native_fields = []
        native_labels = []
        for record in records:
            handle = cls._positive_handle(record.get("handle"))
            chain = cls._handle_chain(record.get("parent_chain"))
            if (
                handle is None
                or record.get("visible") is not True
                or document_handle not in chain
            ):
                continue

            class_bucket = cls._class_bucket(record.get("class_name"))
            bounds = cls._record_bounds(record)
            if bounds is None or not cls._fully_within(bounds, document_bounds):
                continue

            if class_bucket in cls.FIELD_CLASS_TO_KIND:
                native_fields.append((record, bounds, chain, class_bucket))
            elif class_bucket in cls.LABEL_CLASSES:
                text = record.get("title")
                if isinstance(text, str) and text.strip() and not cls._is_generic_label(text):
                    native_labels.append((record, bounds, chain, text.strip()))

        # A Win32 ComboBox can expose its editable child as a separate Edit HWND.
        # Prefer the logical ComboBox surface and omit any Edit descendant of it.
        combo_handles = {
            handle
            for record, _bounds, _chain, bucket in native_fields
            if bucket == "combobox"
            and (handle := cls._positive_handle(record.get("handle"))) is not None
        }
        logical_fields = [
            field
            for field in native_fields
            if not (
                field[3] == "edit"
                and any(
                    combo_handle in field[2][1:]
                    for combo_handle in combo_handles
                )
            )
        ]

        # Label selection is calculated before ScreenElements are emitted.
        # A single static label HWND cannot label two different native fields.
        matches = []
        for field_record, field_bounds, field_chain, class_bucket in logical_fields:
            candidates = []
            for label_record, label_bounds, label_chain, label in native_labels:
                if not cls._same_native_group(
                    field_chain,
                    label_chain,
                    document_handle=document_handle,
                ):
                    continue
                score = cls._label_relation_score(field_bounds, label_bounds)
                if score is not None:
                    label_handle = cls._positive_handle(label_record.get("handle"))
                    if label_handle is not None:
                        candidates.append((score, label, label_handle))

            if not candidates:
                continue

            best_score = min(candidate[0] for candidate in candidates)
            best = [candidate for candidate in candidates if candidate[0] == best_score]
            # If the closest label is tied, do not invent a semantic field.
            if len(best) != 1:
                continue

            _score, label, label_handle = best[0]
            matches.append(
                (field_record, field_bounds, field_chain, class_bucket, label, label_handle)
            )

        label_use_counts = {}
        for _record, _bounds, _chain, _bucket, _label, label_handle in matches:
            label_use_counts[label_handle] = label_use_counts.get(label_handle, 0) + 1

        elements = []
        for (
            field_record,
            field_bounds,
            _field_chain,
            class_bucket,
            label,
            label_handle,
        ) in matches:
            # If one label is the best candidate for multiple fields, fail closed
            # rather than manufacturing duplicate semantic fields.
            if label_use_counts.get(label_handle) != 1:
                continue

            handle = cls._positive_handle(field_record.get("handle"))
            if handle is None:
                continue

            left, top, right, bottom = field_bounds
            width, height = right - left, bottom - top
            if width <= 0 or height <= 0:
                continue

            element_id = f"win32:{handle}"
            kind = cls.FIELD_CLASS_TO_KIND[class_bucket]
            value = field_record.get("title")
            current_value = value.strip() if isinstance(value, str) else None
            if current_value == "":
                current_value = None

            evidence = (
                SemanticEvidence(
                    source=EvidenceSource.ACCESSIBILITY,
                    kind=EvidenceKind.LABEL,
                    value=label,
                    confidence=0.96,
                    element_id=element_id,
                ),
                SemanticEvidence(
                    source=EvidenceSource.ACCESSIBILITY,
                    kind=EvidenceKind.ROLE,
                    value=kind,
                    confidence=0.96,
                    element_id=element_id,
                ),
                SemanticEvidence(
                    source=EvidenceSource.ACCESSIBILITY,
                    kind=EvidenceKind.BOUNDS,
                    value=(
                        left - root_left,
                        top - root_top,
                        width,
                        height,
                    ),
                    confidence=0.96,
                    element_id=element_id,
                ),
            )

            elements.append(
                ScreenElement(
                    kind=kind,
                    label=label,
                    x=left - root_left,
                    y=top - root_top,
                    width=width,
                    height=height,
                    confidence=0.96,
                    metadata={
                        "source": "windowhub_win32_form_provider",
                        "protect_control_type_from_text_fusion": True,
                        "provider_element_id": element_id,
                        "semantic_name": label,
                        "current_value": current_value,
                        "document_scope": document_label,
                        "scope_status": "active_document",
                        "native_handle": handle,
                        "native_control_class": class_bucket,
                        "interaction_capability": InteractionCapability.UNKNOWN.value,
                        "semantic_evidence": evidence,
                    },
                    interaction_capability=InteractionCapability.UNKNOWN,
                    evidence=evidence,
                )
            )

        return tuple(elements)

    @staticmethod
    def _resolve_selected_document_label(
        observation: EnvironmentObservation,
        root_handle: int,
    ) -> str | None:
        """Resolve the selected document using the same semantic UIA contract.

        Reuse the existing UIA provider's labels and selection metadata so the
        native scope key exactly matches the active-document label later used
        by PerceptionEngine and WindowHubFormReader.
        """
        if WindowHubWin32FormProvider._positive_handle(
            (observation.metadata or {}).get("window_handle")
        ) != root_handle:
            return None
        try:
            from app.agent.perception.windowhub_ui_automation_provider import (
                WindowHubUIAutomationProvider,
            )

            elements = WindowHubUIAutomationProvider().perceive(observation)
        except Exception:
            return None

        selected = [
            element.label.strip()
            for element in elements
            if (
                element.kind.casefold() == "tabitem"
                and isinstance(element.label, str)
                and element.label.strip()
                and isinstance(element.metadata, dict)
                and element.metadata.get("uia_tab_scope") == "document"
                and element.metadata.get("uia_document_tab_selected") is True
            )
        ]
        # Fail closed unless UIA resolves exactly one selected document tab.
        return selected[0] if len(selected) == 1 else None

    @classmethod
    def _snapshot_native_windows(
        cls,
        root_handle: int,
    ) -> tuple[dict[str, object], ...] | None:
        """Take a value-in-memory-only Win32 snapshot of descendants."""
        if os.name != "nt":
            return None

        try:
            user32 = ctypes.WinDLL("user32", use_last_error=True)

            get_text_length = user32.GetWindowTextLengthW
            get_text_length.argtypes = (ctypes.c_void_p,)
            get_text_length.restype = ctypes.c_int

            get_text = user32.GetWindowTextW
            get_text.argtypes = (ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_int)
            get_text.restype = ctypes.c_int

            get_class = user32.GetClassNameW
            get_class.argtypes = (ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_int)
            get_class.restype = ctypes.c_int

            is_visible = user32.IsWindowVisible
            is_visible.argtypes = (ctypes.c_void_p,)
            is_visible.restype = ctypes.c_int

            get_window_rect = user32.GetWindowRect
            get_window_rect.argtypes = (ctypes.c_void_p, ctypes.POINTER(_RECT))
            get_window_rect.restype = ctypes.c_int

            get_client_rect = user32.GetClientRect
            get_client_rect.argtypes = (ctypes.c_void_p, ctypes.POINTER(_RECT))
            get_client_rect.restype = ctypes.c_int

            client_to_screen = user32.ClientToScreen
            client_to_screen.argtypes = (ctypes.c_void_p, ctypes.POINTER(_POINT))
            client_to_screen.restype = ctypes.c_int

            enum_child_windows = user32.EnumChildWindows
            callback_type = ctypes.WINFUNCTYPE(
                ctypes.c_int,
                ctypes.c_void_p,
                ctypes.c_ssize_t,
            )
            enum_child_windows.argtypes = (
                ctypes.c_void_p,
                callback_type,
                ctypes.c_ssize_t,
            )
            enum_child_windows.restype = ctypes.c_int

            get_parent = user32.GetParent
            get_parent.argtypes = (ctypes.c_void_p,)
            get_parent.restype = ctypes.c_void_p

            def read_text(hwnd):
                length = max(0, int(get_text_length(hwnd)))
                buffer = ctypes.create_unicode_buffer(min(length + 1, 16384))
                if buffer:
                    get_text(hwnd, buffer, len(buffer))
                return buffer.value

            def window_bounds(hwnd):
                rect = _RECT()
                if not get_window_rect(hwnd, ctypes.byref(rect)):
                    return None
                values = (
                    int(rect.left), int(rect.top),
                    int(rect.right), int(rect.bottom),
                )
                return values if values[2] > values[0] and values[3] > values[1] else None

            def client_bounds(hwnd):
                rect = _RECT()
                if not get_client_rect(hwnd, ctypes.byref(rect)):
                    return None
                first = _POINT(rect.left, rect.top)
                last = _POINT(rect.right, rect.bottom)
                if not (
                    client_to_screen(hwnd, ctypes.byref(first))
                    and client_to_screen(hwnd, ctypes.byref(last))
                ):
                    return None
                values = (int(first.x), int(first.y), int(last.x), int(last.y))
                return values if values[2] > values[0] and values[3] > values[1] else None

            def parent_chain(handle):
                chain = [handle]
                current = handle
                for _ in range(64):
                    parent = cls._positive_handle(get_parent(ctypes.c_void_p(current)))
                    if parent is None or parent == current:
                        break
                    chain.append(parent)
                    current = parent
                return tuple(chain)

            records = []

            def callback(raw_handle, _lparam):
                handle = cls._positive_handle(raw_handle)
                if handle is None:
                    return True

                hwnd = ctypes.c_void_p(handle)
                title = read_text(hwnd)
                class_buffer = ctypes.create_unicode_buffer(256)
                get_class(hwnd, class_buffer, len(class_buffer))

                records.append({
                    "handle": handle,
                    "title": title,
                    "class_name": class_buffer.value,
                    "visible": bool(is_visible(hwnd)),
                    "bounds": window_bounds(hwnd),
                    "client_bounds": client_bounds(hwnd),
                    "parent_chain": parent_chain(handle),
                })
                return True

            callback_ref = callback_type(callback)
            if not enum_child_windows(
                ctypes.c_void_p(root_handle),
                callback_ref,
                0,
            ):
                return None
            return tuple(records)
        except Exception:
            return None

    @staticmethod
    def _positive_handle(value) -> int | None:
        try:
            if hasattr(value, "value"):
                value = value.value
            handle = int(value)
        except (TypeError, ValueError, OverflowError, OSError):
            return None
        return handle if handle > 0 else None

    @classmethod
    def _handle_chain(cls, value) -> tuple[int, ...]:
        if not isinstance(value, (tuple, list)):
            return ()
        result = []
        for item in value:
            handle = cls._positive_handle(item)
            if handle is not None:
                result.append(handle)
        return tuple(result)

    @staticmethod
    def _normalized_text(value) -> str:
        if not isinstance(value, str):
            return ""
        return " ".join(value.split()).casefold()

    @classmethod
    def _class_bucket(cls, value) -> str | None:
        if not isinstance(value, str):
            return None
        normalized = value.strip().casefold()
        if normalized in {"edit"}:
            return "edit"
        if normalized in {"combobox", "combo"}:
            return "combobox"
        if normalized in {"static", "text"}:
            return "static"
        return None

    @staticmethod
    def _valid_bounds(value) -> tuple[int, int, int, int] | None:
        if not isinstance(value, (tuple, list)) or len(value) != 4:
            return None
        try:
            bounds = tuple(int(part) for part in value)
        except (TypeError, ValueError, OverflowError):
            return None
        if bounds[2] <= bounds[0] or bounds[3] <= bounds[1]:
            return None
        return bounds

    @classmethod
    def _record_bounds(cls, record) -> tuple[int, int, int, int] | None:
        return (
            cls._valid_bounds(record.get("client_bounds"))
            or cls._valid_bounds(record.get("bounds"))
        )

    @staticmethod
    def _fully_within(
        inner: tuple[int, int, int, int],
        outer: tuple[int, int, int, int],
    ) -> bool:
        return (
            inner[0] >= outer[0]
            and inner[1] >= outer[1]
            and inner[2] <= outer[2]
            and inner[3] <= outer[3]
        )

    @classmethod
    def _same_native_group(
        cls,
        left_chain: tuple[int, ...],
        right_chain: tuple[int, ...],
        *,
        document_handle: int,
    ) -> bool:
        """Require actual sibling/shared container within the document.

        The WindowHub root is a common ancestor of every control and therefore
        is not sufficient evidence that a static label belongs to a field.
        Direct children of the selected document may share the document HWND;
        nested controls must share a more specific ancestor before that HWND.
        """
        if len(left_chain) < 2 or len(right_chain) < 2:
            return False
        if document_handle not in left_chain or document_handle not in right_chain:
            return False

        # Direct children of the selected document can share its HWND as parent.
        if left_chain[1] == document_handle and right_chain[1] == document_handle:
            return True

        left_document_index = left_chain.index(document_handle)
        right_document_index = right_chain.index(document_handle)
        left_scoped_ancestors = set(left_chain[1:left_document_index])
        right_scoped_ancestors = set(right_chain[1:right_document_index])

        # Do not treat the main WindowHub root or any ancestor above the document
        # as a shared control container.
        return bool(left_scoped_ancestors.intersection(right_scoped_ancestors))

    @classmethod
    def _label_relation_score(
        cls,
        field_bounds: tuple[int, int, int, int],
        label_bounds: tuple[int, int, int, int],
    ) -> int | None:
        fl, ft, fr, fb = field_bounds
        ll, lt, lr, lb = label_bounds
        field_center_y = (ft + fb) / 2
        label_center_y = (lt + lb) / 2
        same_row = abs(field_center_y - label_center_y) <= max(
            18,
            1.5 * max(fb - ft, lb - lt),
        )
        left_gap = fl - lr
        if same_row and -8 <= left_gap <= 220:
            return max(0, left_gap)

        horizontal_overlap = ll < fr and lr > fl
        above_gap = ft - lb
        if horizontal_overlap and -8 <= above_gap <= 90:
            return 221 + max(0, above_gap)
        return None

    @staticmethod
    def _is_generic_label(value: str) -> bool:
        normalized = " ".join(value.split()).casefold()
        return normalized in {
            "",
            "layoutitem",
            "comboboxedit",
            "dateedit",
            "textbox",
            "edit",
            "control",
        }
