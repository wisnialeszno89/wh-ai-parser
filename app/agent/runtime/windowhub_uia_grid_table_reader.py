"""Bounded, read-only adapter for Windows UIA GridPattern tables.

The resolver must re-find the target in the current observed window on every
call. This module never caches UIA wrappers and never performs UI actions.

WindowHub lookup grids can contain business records. Register this reader with
the business_records classification so the default observation broker denies
it unless local policy explicitly authorizes that data class.
"""

from collections.abc import Callable, Mapping
import json
import time

from app.agent.perception.screen_element import ScreenElement
from app.agent.runtime.read_only_observation_broker import (
    ObservationCapabilitySpec,
    ObservationReadContext,
    ObservationReadResult,
    ObservationRejected,
)


MAX_UIA_GRID_COLUMNS = 64
MAX_UIA_GRID_CELL_TEXT = 1_000
WINDOWHUB_GRID_CAPABILITY_NAME = "windowhub_read_grid_page"


def windowhub_grid_capability_spec(
    *,
    max_items: int = 10,
    timeout_seconds: float = 3.0,
    max_result_bytes: int = 8_192,
) -> ObservationCapabilitySpec:
    """Return the WindowHub grid capability with a fail-closed data class."""
    return ObservationCapabilitySpec(
        name=WINDOWHUB_GRID_CAPABILITY_NAME,
        description="Read one bounded page from a WindowHub UIA data grid.",
        input_contract="table_page_v1",
        max_items=max_items,
        data_classification="business_records",
        evidence_source="uia_grid",
        timeout_seconds=timeout_seconds,
        max_result_bytes=max_result_bytes,
        read_only=True,
    )


class WindowHubUIAGridTableReader:
    """Read a bounded page from a freshly resolved UIA GridPattern target."""

    def __init__(
        self,
        *,
        grid_resolver: Callable[[ScreenElement], object],
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if not callable(grid_resolver):
            raise TypeError("uia_grid_resolver_must_be_callable")
        self._grid_resolver = grid_resolver
        self._clock = clock

    def __call__(
        self,
        target: ScreenElement,
        parameters: Mapping[str, object],
        context: ObservationReadContext,
    ) -> ObservationReadResult:
        metadata = target.metadata or {}
        control_type = metadata.get("uia_control_type")
        runtime_id = metadata.get("uia_runtime_id")
        if (
            target.kind != "table"
            or control_type not in {"datagrid", "table"}
            or not isinstance(runtime_id, str)
            or not runtime_id.strip()
        ):
            raise ObservationRejected(
                "observation_rejected:uia_grid_target_invalid"
            )

        offset = parameters.get("offset")
        limit = parameters.get("limit")
        if (
            isinstance(offset, bool)
            or not isinstance(offset, int)
            or offset < 0
            or isinstance(limit, bool)
            or not isinstance(limit, int)
            or not 1 <= limit <= context.max_items
        ):
            raise ObservationRejected(
                "observation_rejected:uia_grid_page_parameters_invalid"
            )
        text_query = parameters.get("text_query")
        if text_query not in (None, ""):
            raise ObservationRejected(
                "observation_rejected:uia_grid_text_query_unsupported"
            )

        self._check_deadline(context)
        try:
            grid = self._grid_resolver(target)
        except Exception as exc:
            raise ObservationRejected(
                f"observation_rejected:uia_grid_resolution_failed:{type(exc).__name__}"
            ) from exc
        self._check_deadline(context)

        self._verify_resolved_identity(grid, runtime_id, control_type)
        grid_pattern = self._pattern(grid, "iface_grid")
        row_count = self._count(
            getattr(grid_pattern, "CurrentRowCount", None),
            "row_count",
            minimum=0,
            maximum=1_000_000_000,
        )
        column_count = self._count(
            getattr(grid_pattern, "CurrentColumnCount", None),
            "column_count",
            minimum=1,
            maximum=MAX_UIA_GRID_COLUMNS,
        )
        self._check_deadline(context)

        headers, header_limitations = self._read_headers(
            grid,
            column_count,
            context,
        )
        rows = []
        limitations = list(header_limitations)
        end = min(row_count, offset + limit)

        for row_index in range(offset, end):
            self._check_deadline(context)
            row = []
            for column_index in range(column_count):
                self._check_deadline(context)
                try:
                    cell = grid_pattern.GetItem(row_index, column_index)
                except Exception as exc:
                    raise ObservationRejected(
                        "observation_rejected:uia_grid_cell_unavailable"
                    ) from exc
                self._check_deadline(context)
                value = self._read_element_text(cell)
                if value is not None and len(value) > MAX_UIA_GRID_CELL_TEXT:
                    raise ObservationRejected(
                        "observation_rejected:uia_grid_cell_text_too_long"
                    )
                row.append(value)
            rows.append(row)
            self._check_result_budget(
                headers,
                rows,
                offset,
                end < row_count,
                row_count,
                context.max_result_bytes,
            )

        if not rows and row_count > offset:
            limitations.append(
                "The requested page returned no readable rows although UIA reports more rows."
            )

        content = {
            "headers": headers,
            "rows": rows,
            "offset": offset,
            "has_more": end < row_count,
            "reported_row_count": row_count,
        }
        self._check_result_budget(
            headers,
            rows,
            offset,
            end < row_count,
            row_count,
            context.max_result_bytes,
        )
        limitations.append(
            "UIA-reported row count is provider metadata and is not independently verified as a record count."
        )
        self._check_deadline(context)
        return ObservationReadResult(
            content=content,
            limitations=tuple(limitations),
            confidence=0.95,
        )

    def _read_headers(
        self,
        grid: object,
        column_count: int,
        context: ObservationReadContext,
    ) -> tuple[list[str], tuple[str, ...]]:
        labels: list[str] = []
        try:
            table_pattern = self._pattern(grid, "iface_table")
            getter = getattr(table_pattern, "GetCurrentColumnHeaders", None)
            if callable(getter):
                self._check_deadline(context)
                raw_headers = getter()
                self._check_deadline(context)
                candidates = list(raw_headers) if raw_headers is not None else []
                if len(candidates) == column_count:
                    labels = [
                        self._read_element_text(item) or ""
                        for item in candidates
                    ]
        except Exception:
            labels = []

        limitations: list[str] = []
        if len(labels) != column_count:
            labels = []
        if not labels or any(not value.strip() for value in labels):
            limitations.append(
                "UIA did not provide all column header labels; positional labels are used for missing headers."
            )
            labels = [
                value.strip() if index < len(labels) and value.strip()
                else f"Column {index + 1}"
                for index, value in enumerate(
                    labels + [""] * max(0, column_count - len(labels))
                )
            ]
        if any(len(value) > 128 for value in labels):
            raise ObservationRejected(
                "observation_rejected:uia_grid_header_too_long"
            )
        return labels, tuple(limitations)

    def _pattern(self, element: object, attribute: str):
        try:
            value = getattr(element, attribute)
        except Exception as exc:
            raise ObservationRejected(
                f"observation_rejected:uia_grid_{attribute}_unavailable"
            ) from exc
        if value is None:
            raise ObservationRejected(
                f"observation_rejected:uia_grid_{attribute}_unavailable"
            )
        return value

    @staticmethod
    def _count(
        value: object,
        name: str,
        *,
        minimum: int,
        maximum: int,
    ) -> int:
        if (
            isinstance(value, bool)
            or not isinstance(value, int)
            or not minimum <= value <= maximum
        ):
            raise ObservationRejected(
                f"observation_rejected:uia_grid_{name}_invalid"
            )
        return value

    @staticmethod
    def _verify_resolved_identity(
        grid: object,
        expected_runtime_id: str,
        expected_control_type: str,
    ) -> None:
        try:
            info = grid.element_info
            actual_runtime_id = getattr(info, "runtime_id", None)
            actual_type = str(
                getattr(info, "control_type", "")
            ).strip().casefold()
        except Exception as exc:
            raise ObservationRejected(
                "observation_rejected:uia_grid_resolved_identity_unavailable"
            ) from exc

        if isinstance(actual_runtime_id, (tuple, list)):
            actual_runtime_id = "-".join(
                str(part) for part in actual_runtime_id
            )
        elif actual_runtime_id is not None:
            actual_runtime_id = str(actual_runtime_id)

        if (
            actual_runtime_id != expected_runtime_id
            or actual_type != expected_control_type
        ):
            raise ObservationRejected(
                "observation_rejected:uia_grid_resolved_identity_mismatch"
            )

    @staticmethod
    def _read_element_text(element: object) -> str | None:
        candidate = element
        if not hasattr(candidate, "element_info"):
            try:
                from pywinauto.controls.uiawrapper import UIAWrapper
                from pywinauto.windows.uia_element_info import UIAElementInfo

                candidate = UIAWrapper(UIAElementInfo(element))
            except Exception:
                candidate = element

        element_info = getattr(candidate, "element_info", None)
        for owner, attribute_name in (
            (element_info, "name"),
            (element_info, "rich_text"),
            (candidate, "window_text"),
            (candidate, "get_value"),
            (candidate, "CurrentName"),
        ):
            try:
                if owner is None:
                    continue
                source = getattr(owner, attribute_name, None)
                value = source() if callable(source) else source
            except Exception:
                continue
            if isinstance(value, str):
                cleaned = value.strip()
                if cleaned:
                    return cleaned

        for interface_name, property_name in (
            ("iface_value", "CurrentValue"),
            ("iface_legacy_iaccessible", "CurrentValue"),
        ):
            try:
                interface = getattr(candidate, interface_name)
                value = getattr(interface, property_name)
            except Exception:
                continue
            if isinstance(value, str) and value.strip():
                return value.strip()

        return None

    @staticmethod
    def _check_result_budget(
        headers: list[str],
        rows: list[list[str | None]],
        offset: int,
        has_more: bool,
        row_count: int,
        max_bytes: int,
    ) -> None:
        payload = {
            "headers": headers,
            "rows": rows,
            "offset": offset,
            "has_more": has_more,
            "reported_row_count": row_count,
        }
        encoded = json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        ).encode("utf-8")
        if len(encoded) > max_bytes:
            raise ObservationRejected(
                "observation_rejected:uia_grid_result_byte_budget_exceeded"
            )

    def _check_deadline(self, context: ObservationReadContext) -> None:
        if self._clock() > context.deadline_monotonic:
            raise ObservationRejected(
                "observation_rejected:uia_grid_time_budget_exceeded"
            )
