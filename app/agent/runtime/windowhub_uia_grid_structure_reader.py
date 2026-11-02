"""Structure-only UIA reader for WindowHub grids.

This reader exposes structural metadata only. It never requests GridPattern
cells, table headers, row text, customer names or other business-record data.
It is safe to register under the broker default ui_structure policy.
"""

from collections.abc import Callable, Mapping
import time

from app.agent.perception.screen_element import ScreenElement
from app.agent.runtime.read_only_observation_broker import (
    ObservationCapabilitySpec,
    ObservationReadContext,
    ObservationReadResult,
    ObservationRejected,
)


WINDOWHUB_GRID_STRUCTURE_CAPABILITY_NAME = "windowhub_inspect_grid_structure"
_ALLOWED_FIELDS = frozenset(
    {
        "row_count",
        "column_count",
        "grid_pattern_available",
        "table_pattern_available",
    }
)


def windowhub_grid_structure_capability_spec(
    *,
    max_items: int = 10,
    timeout_seconds: float = 2.0,
    max_result_bytes: int = 2_048,
) -> ObservationCapabilitySpec:
    """Build a least-privilege capability for table structure inspection."""
    return ObservationCapabilitySpec(
        name=WINDOWHUB_GRID_STRUCTURE_CAPABILITY_NAME,
        description=(
            "Inspect structural metadata of a visible WindowHub table "
            "without reading any cells or business records."
        ),
        input_contract="entity_inspection_v1",
        max_items=max_items,
        data_classification="ui_structure",
        evidence_source="uia_grid_structure",
        timeout_seconds=timeout_seconds,
        max_result_bytes=max_result_bytes,
        read_only=True,
    )


class WindowHubUIAGridStructureReader:
    """Return requested GridPattern dimensions and pattern availability only."""

    def __init__(
        self,
        *,
        grid_resolver: Callable[[ScreenElement], object],
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if not callable(grid_resolver):
            raise TypeError("uia_grid_structure_resolver_must_be_callable")
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
            or metadata.get("source") != "windowhub_ui_automation"
            or control_type not in {"datagrid", "table"}
            or not isinstance(runtime_id, str)
            or not runtime_id.strip()
        ):
            raise ObservationRejected(
                "observation_rejected:uia_grid_structure_target_invalid"
            )

        fields = parameters.get("fields")
        if not isinstance(fields, (list, tuple)) or not fields:
            raise ObservationRejected(
                "observation_rejected:uia_grid_structure_fields_invalid"
            )
        if any(
            not isinstance(name, str) or name not in _ALLOWED_FIELDS
            for name in fields
        ):
            raise ObservationRejected(
                "observation_rejected:uia_grid_structure_field_not_allowed"
            )
        if len(fields) != len(set(fields)):
            raise ObservationRejected(
                "observation_rejected:uia_grid_structure_duplicate_field"
            )

        self._check_deadline(context)
        try:
            grid = self._grid_resolver(target)
        except Exception as exc:
            raise ObservationRejected(
                f"observation_rejected:uia_grid_structure_resolution_failed:{type(exc).__name__}"
            ) from exc
        self._check_deadline(context)
        self._verify_identity(grid, runtime_id, control_type)

        result: dict[str, object] = {}
        grid_pattern = self._optional_pattern(grid, "iface_grid")
        table_pattern = self._optional_pattern(grid, "iface_table")

        for field_name in fields:
            self._check_deadline(context)
            if field_name == "grid_pattern_available":
                result[field_name] = grid_pattern is not None
            elif field_name == "table_pattern_available":
                result[field_name] = table_pattern is not None
            elif field_name in {"row_count", "column_count"}:
                if grid_pattern is None:
                    raise ObservationRejected(
                        "observation_rejected:uia_grid_structure_grid_pattern_unavailable"
                    )
                attribute = (
                    "CurrentRowCount"
                    if field_name == "row_count"
                    else "CurrentColumnCount"
                )
                try:
                    value = getattr(grid_pattern, attribute)
                except Exception as exc:
                    raise ObservationRejected(
                        f"observation_rejected:uia_grid_structure_{field_name}_unavailable"
                    ) from exc
                if (
                    isinstance(value, bool)
                    or not isinstance(value, int)
                    or value < 0
                    or value > 1_000_000_000
                ):
                    raise ObservationRejected(
                        f"observation_rejected:uia_grid_structure_{field_name}_invalid"
                    )
                result[field_name] = value

        self._check_deadline(context)
        limitations = (
            "UIA row and column counts are provider-reported structural metadata, not verified record counts.",
            "No table cells, row text, column header text or business-record values were read.",
        )
        return ObservationReadResult(
            content={"fields": result},
            limitations=limitations,
            confidence=0.99,
        )

    @staticmethod
    def _optional_pattern(element: object, attribute: str):
        try:
            value = getattr(element, attribute, None)
        except Exception:
            return None
        return value

    @staticmethod
    def _verify_identity(
        grid: object,
        expected_runtime_id: str,
        expected_control_type: str,
    ) -> None:
        try:
            info = grid.element_info
            actual_runtime_id = getattr(info, "runtime_id", None)
            actual_control_type = str(
                getattr(info, "control_type", "")
            ).strip().casefold()
        except Exception as exc:
            raise ObservationRejected(
                "observation_rejected:uia_grid_structure_identity_unavailable"
            ) from exc

        if isinstance(actual_runtime_id, (tuple, list)):
            actual_runtime_id = "-".join(
                str(part) for part in actual_runtime_id
            )
        elif actual_runtime_id is not None:
            actual_runtime_id = str(actual_runtime_id)

        if (
            actual_runtime_id != expected_runtime_id
            or actual_control_type != expected_control_type
        ):
            raise ObservationRejected(
                "observation_rejected:uia_grid_structure_identity_mismatch"
            )

    def _check_deadline(self, context: ObservationReadContext) -> None:
        if self._clock() > context.deadline_monotonic:
            raise ObservationRejected(
                "observation_rejected:uia_grid_structure_time_budget_exceeded"
            )
