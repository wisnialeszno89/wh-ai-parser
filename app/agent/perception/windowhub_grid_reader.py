from __future__ import annotations

from dataclasses import dataclass

from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.screen_scene import ScreenScene


@dataclass(frozen=True)
class WindowHubGridCell:
    """Read-only observation of one UIA grid cell."""

    row_index: int
    column_index: int
    label: str
    value: str | None
    value_available: bool
    document_scope: str | None
    value_source: str | None
    confidence: float | None
    element: ScreenElement

    def to_payload(self) -> dict[str, object]:
        """Return model-safe cell data without provider IDs or coordinates."""
        value_available = self.value_available and isinstance(self.value, str)
        return {
            "row_index": self.row_index,
            "column_index": self.column_index,
            "label": self.label,
            "current_value": self.value if value_available else None,
            "value_available": value_available,
            "confidence": self.confidence,
        }


@dataclass(frozen=True)
class WindowHubGrid:
    """Read-only rectangular view of the observed cells in one UIA grid."""

    grid_id: str
    document_scope: str | None
    scope_status: str
    row_count: int
    column_count: int
    rows: tuple[tuple[WindowHubGridCell | None, ...], ...]
    cells: tuple[WindowHubGridCell, ...]
    duplicate_positions: tuple[tuple[int, int], ...] = ()
    shape_consistent: bool = True
    truncated: bool = False
    matrix_omitted: bool = False

    @property
    def observed_cell_count(self) -> int:
        return len(self.cells)

    @property
    def missing_cell_count(self) -> int:
        return sum(
            1
            for row in self.rows
            for cell in row
            if cell is None
        ) if self.rows else (
            max(0, self.row_count * self.column_count - len(self.cells))
            if self.matrix_omitted
            else 0
        )

    @property
    def unreadable_value_count(self) -> int:
        return sum(1 for cell in self.cells if not cell.value_available)

    @property
    def complete(self) -> bool:
        """True only when shape, every cell, and every value were observed."""
        expected = self.row_count * self.column_count
        return (
            not self.matrix_omitted
            and self.shape_consistent
            and not self.truncated
            and not self.duplicate_positions
            and self.observed_cell_count == expected
            and self.missing_cell_count == 0
            and self.unreadable_value_count == 0
        )

    def to_payload(self) -> dict[str, object]:
        """
        Serialize structured grid data without leaking provider-local IDs,
        window handles, screen geometry, or raw ScreenElement metadata.
        """
        payload: dict[str, object] = {
            "document_scope": self.document_scope,
            "scope_status": self.scope_status,
            "row_count": self.row_count,
            "column_count": self.column_count,
            "complete": self.complete,
            "shape_consistent": self.shape_consistent,
            "truncated": self.truncated,
            "matrix_omitted": self.matrix_omitted,
            "observed_cell_count": self.observed_cell_count,
            "missing_cell_count": self.missing_cell_count,
            "unreadable_value_count": self.unreadable_value_count,
            "duplicate_positions": [
                {"row_index": row, "column_index": column}
                for row, column in self.duplicate_positions
            ],
        }

        if self.matrix_omitted:
            # Keep observed evidence available without allocating/sending a
            # dense matrix whose dimensions exceed the reader's cap.
            payload["observed_cells"] = [
                cell.to_payload() for cell in self.cells
            ]
        else:
            payload["rows"] = [
                [
                    cell.to_payload() if cell is not None else None
                    for cell in row
                ]
                for row in self.rows
            ]

        if self.duplicate_positions:
            duplicate_positions = set(self.duplicate_positions)
            payload["duplicate_cells"] = [
                cell.to_payload()
                for cell in self.cells
                if (cell.row_index, cell.column_index) in duplicate_positions
            ]

        return payload


class WindowHubGridReader:
    """
    Groups UIA grid-cell observations into read-only row/column matrices.

    This reader consumes ScreenScene evidence only; it does not create COM
    objects, inspect live windows, or execute GUI actions. Active-document
    reads fail closed if the scene has not resolved a single active document.
    """

    MAX_MATRIX_CELLS = 10_000

    def read(self, scene: ScreenScene) -> tuple[WindowHubGrid, ...]:
        active_document = scene.active_document
        groups: dict[tuple[str | None, str], list[tuple[WindowHubGridCell, int, int, bool]]] = {}

        for element in scene.elements:
            metadata = element.metadata or {}
            if metadata.get("uia_grid_cell_observation") is not True:
                continue

            grid_id = metadata.get("uia_grid_id")
            if not isinstance(grid_id, str) or not grid_id.strip():
                continue

            label = element.label.strip() if isinstance(element.label, str) else ""
            if not label:
                continue

            row_index = self._nonnegative_int(metadata.get("uia_grid_row_index"))
            column_index = self._nonnegative_int(metadata.get("uia_grid_column_index"))
            row_count = self._positive_int(metadata.get("uia_grid_row_count"))
            column_count = self._positive_int(metadata.get("uia_grid_column_count"))

            if (
                row_index is None
                or column_index is None
                or row_count is None
                or column_count is None
                or row_index >= row_count
                or column_index >= column_count
            ):
                continue

            raw_scope = metadata.get("document_scope")
            document_scope = (
                raw_scope.strip()
                if isinstance(raw_scope, str) and raw_scope.strip()
                else None
            )
            raw_value = metadata.get("current_value")
            value_available = (
                metadata.get("current_value_available") is True
                and isinstance(raw_value, str)
            )
            value = raw_value if value_available else None
            raw_source = metadata.get("current_value_source")
            value_source = (
                raw_source.strip()
                if isinstance(raw_source, str) and raw_source.strip()
                else None
            )

            cell = WindowHubGridCell(
                row_index=row_index,
                column_index=column_index,
                label=label,
                value=value,
                value_available=value_available,
                document_scope=document_scope,
                value_source=value_source,
                confidence=element.confidence,
                element=element,
            )
            key = (document_scope, grid_id.strip())
            groups.setdefault(key, []).append(
                (
                    cell,
                    row_count,
                    column_count,
                    metadata.get("uia_grid_enumeration_truncated") is True,
                )
            )

        grids = [
            self._build_grid(
                grid_id=grid_id,
                document_scope=scope,
                active_document=active_document,
                entries=entries,
            )
            for (scope, grid_id), entries in groups.items()
        ]
        grids.sort(key=lambda grid: (grid.document_scope or "", grid.grid_id))
        return tuple(grids)

    def read_active_document(self, scene: ScreenScene) -> tuple[WindowHubGrid, ...]:
        active_document = scene.active_document
        if active_document is None:
            return ()
        return tuple(
            grid
            for grid in self.read(scene)
            if grid.scope_status == "active_document"
        )

    @classmethod
    def _build_grid(
        cls,
        *,
        grid_id: str,
        document_scope: str | None,
        active_document: str | None,
        entries: list[tuple[WindowHubGridCell, int, int, bool]],
    ) -> WindowHubGrid:
        dimensions = {(rows, columns) for _, rows, columns, _ in entries}
        shape_consistent = len(dimensions) == 1
        row_count = max(rows for rows, _ in dimensions)
        column_count = max(columns for _, columns in dimensions)
        truncated = any(entry[3] for entry in entries)
        cells = tuple(
            sorted(
                (entry[0] for entry in entries),
                key=lambda cell: (cell.row_index, cell.column_index, cell.label),
            )
        )

        cells_by_position: dict[tuple[int, int], list[WindowHubGridCell]] = {}
        for cell in cells:
            cells_by_position.setdefault(
                (cell.row_index, cell.column_index), []
            ).append(cell)

        duplicate_positions = tuple(
            sorted(
                position
                for position, matching in cells_by_position.items()
                if len(matching) > 1
            )
        )

        matrix_omitted = row_count * column_count > cls.MAX_MATRIX_CELLS
        if matrix_omitted:
            rows: tuple[tuple[WindowHubGridCell | None, ...], ...] = ()
        else:
            rows = tuple(
                tuple(
                    (
                        matching[0]
                        if len(matching) == 1
                        and (row_index, column_index) not in duplicate_positions
                        else None
                    )
                    for column_index in range(column_count)
                    for matching in (
                        cells_by_position.get((row_index, column_index), []),
                    )
                )
                for row_index in range(row_count)
            )

        if active_document is None:
            scope_status = "unresolved"
        elif document_scope is None:
            scope_status = "unknown"
        elif document_scope == active_document:
            scope_status = "active_document"
        else:
            scope_status = "other_document"

        return WindowHubGrid(
            grid_id=grid_id,
            document_scope=document_scope,
            scope_status=scope_status,
            row_count=row_count,
            column_count=column_count,
            rows=rows,
            cells=cells,
            duplicate_positions=duplicate_positions,
            shape_consistent=shape_consistent,
            truncated=truncated,
            matrix_omitted=matrix_omitted,
        )

    @staticmethod
    def _nonnegative_int(value) -> int | None:
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            return None
        return value

    @staticmethod
    def _positive_int(value) -> int | None:
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            return None
        return value
