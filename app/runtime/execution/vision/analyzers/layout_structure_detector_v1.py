from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LayoutStructure:
    kind: str
    object_indices: tuple[int, ...]


class LayoutStructureDetectorV1:
    """
    Detects simple geometric structures among logical visual objects.

    This layer intentionally does not assign semantic UI meaning.
    It recognizes only spatial organization:
    - horizontal rows
    - vertical stacks
    - two-dimensional grids
    - isolated objects
    """

    def __init__(
        self,
        *,
        row_vertical_tolerance: float = 0.75,
        column_horizontal_tolerance: float = 0.75,
        max_gap_factor: float = 3.0,
    ) -> None:
        self.row_vertical_tolerance = row_vertical_tolerance
        self.column_horizontal_tolerance = column_horizontal_tolerance
        self.max_gap_factor = max_gap_factor

    def detect(self, objects) -> tuple[LayoutStructure, ...]:
        if not objects:
            return ()

        rows = self._build_rows(objects)
        columns = self._build_columns(objects)

        assigned: set[int] = set()
        structures: list[LayoutStructure] = []

        # First identify genuine two-dimensional grids.
        # A grid is formed by the union of compatible rows and columns,
        # rather than by the intersection of one row and one column.
        grid_candidates: list[tuple[int, ...]] = []

        for row in rows:
            for other_row in rows:
                if row >= other_row:
                    continue

                members = tuple(sorted(set(row) | set(other_row)))

                if len(members) < 4:
                    continue

                if self._forms_grid(members, objects):
                    grid_candidates.append(members)

        # Prefer the largest valid grid and avoid overlapping structures.
        grid_candidates.sort(key=len, reverse=True)

        for members in grid_candidates:
            if any(index in assigned for index in members):
                continue

            structures.append(
                LayoutStructure(
                    kind="grid",
                    object_indices=members,
                )
            )
            assigned.update(members)

        # Then identify horizontal rows.
        for row in rows:
            members = tuple(index for index in row if index not in assigned)

            if len(members) >= 2:
                structures.append(
                    LayoutStructure(
                        kind="horizontal_row",
                        object_indices=members,
                    )
                )
                assigned.update(members)

        # Then identify vertical stacks.
        for column in columns:
            members = tuple(index for index in column if index not in assigned)

            if len(members) >= 2:
                structures.append(
                    LayoutStructure(
                        kind="vertical_stack",
                        object_indices=members,
                    )
                )
                assigned.update(members)

        # Everything not belonging to a larger structure is isolated.
        for index in range(len(objects)):
            if index not in assigned:
                structures.append(
                    LayoutStructure(
                        kind="isolated",
                        object_indices=(index,),
                    )
                )

        return tuple(structures)

    def _build_rows(self, objects) -> list[tuple[int, ...]]:
        groups: list[list[int]] = []

        for index, obj in enumerate(objects):
            placed = False

            for group in groups:
                reference = objects[group[0]]

                if self._same_row(reference.bounds, obj.bounds):
                    if self._close_horizontally(reference.bounds, obj.bounds):
                        group.append(index)
                        placed = True
                        break

            if not placed:
                groups.append([index])

        return [
            tuple(
                sorted(
                    group,
                    key=lambda index: objects[index].bounds.x,
                )
            )
            for group in groups
            if len(group) >= 2
        ]

    def _build_columns(self, objects) -> list[tuple[int, ...]]:
        groups: list[list[int]] = []

        for index, obj in enumerate(objects):
            placed = False

            for group in groups:
                reference = objects[group[0]]

                if self._same_column(reference.bounds, obj.bounds):
                    if self._close_vertically(reference.bounds, obj.bounds):
                        group.append(index)
                        placed = True
                        break

            if not placed:
                groups.append([index])

        return [
            tuple(
                sorted(
                    group,
                    key=lambda index: objects[index].bounds.y,
                )
            )
            for group in groups
            if len(group) >= 2
        ]

    def _forms_grid(self, members, objects):
        if len(members) < 4:
            return False

        rows = self._cluster_by_y(members, objects)
        columns = self._cluster_by_x(members, objects)

        # A genuine grid needs at least two rows and two columns.
        if len(rows) < 2 or len(columns) < 2:
            return False

        # Every row and every column must contain at least two objects.
        if any(len(row) < 2 for row in rows):
            return False

        if any(len(column) < 2 for column in columns):
            return False

        # A regular grid must contain the complete row/column matrix.
        expected_count = len(rows) * len(columns)

        if len(members) != expected_count:
            return False

        return True

    def _cluster_by_y(self, members, objects):
        groups: list[list[int]] = []

        for index in sorted(
            members,
            key=lambda i: objects[i].bounds.center[1],
        ):
            obj = objects[index]

            placed = False

            for group in groups:
                reference = objects[group[0]]

                if self._same_row(reference.bounds, obj.bounds):
                    group.append(index)
                    placed = True
                    break

            if not placed:
                groups.append([index])

        return groups

    def _cluster_by_x(self, members, objects):
        groups: list[list[int]] = []

        for index in sorted(
            members,
            key=lambda i: objects[i].bounds.center[0],
        ):
            obj = objects[index]

            placed = False

            for group in groups:
                reference = objects[group[0]]

                if self._same_column(reference.bounds, obj.bounds):
                    group.append(index)
                    placed = True
                    break

            if not placed:
                groups.append([index])

        return groups

    def _same_row(self, current, other) -> bool:
        _, current_y = current.center
        _, other_y = other.center

        tolerance = max(
            current.height,
            other.height,
        ) * self.row_vertical_tolerance

        return abs(current_y - other_y) <= tolerance

    def _same_column(self, current, other) -> bool:
        current_x, _ = current.center
        other_x, _ = other.center

        tolerance = max(
            current.width,
            other.width,
        ) * self.column_horizontal_tolerance

        return abs(current_x - other_x) <= tolerance

    def _close_horizontally(self, current, other) -> bool:
        gap = self._gap(
            current.x,
            current.right,
            other.x,
            other.right,
        )

        return gap <= max(current.width, other.width) * self.max_gap_factor

    def _close_vertically(self, current, other) -> bool:
        gap = self._gap(
            current.y,
            current.bottom,
            other.y,
            other.bottom,
        )

        return gap <= max(current.height, other.height) * self.max_gap_factor

    @staticmethod
    def _gap(start_a, end_a, start_b, end_b) -> int:
        if end_a < start_b:
            return start_b - end_a

        if end_b < start_a:
            return start_a - end_b

        return 0
