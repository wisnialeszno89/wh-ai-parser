from math import hypot

from app.runtime.execution.vision.models.logical_object_context import (
    LogicalObjectContext,
    LogicalObjectNeighbor,
)


class LogicalObjectContextV1:
    """
    Computes purely geometric relationships between reconstructed logical objects.

    This layer intentionally does not assign semantic UI meaning.
    """

    def __init__(
        self,
        *,
        row_vertical_tolerance: float = 0.75,
        column_horizontal_tolerance: float = 0.75,
        overlap_tolerance: float = 0.20,
    ) -> None:
        self.row_vertical_tolerance = row_vertical_tolerance
        self.column_horizontal_tolerance = column_horizontal_tolerance
        self.overlap_tolerance = overlap_tolerance

    def analyze(self, objects) -> tuple[LogicalObjectContext, ...]:
        contexts = []

        for index, current in enumerate(objects):
            left = []
            right = []
            above = []
            below = []
            same_row = []
            same_column = []

            for other_index, other in enumerate(objects):
                if index == other_index:
                    continue

                relation = self._relation(index, current.bounds, other_index, other.bounds)

                if relation is None:
                    continue

                horizontal_gap, vertical_gap, x_overlap, y_overlap, distance = relation

                neighbor = LogicalObjectNeighbor(
                    object_index=other_index,
                    horizontal_gap=horizontal_gap,
                    vertical_gap=vertical_gap,
                    x_overlap_ratio=x_overlap,
                    y_overlap_ratio=y_overlap,
                    center_distance=distance,
                )

                if self._is_same_row(current.bounds, other.bounds):
                    same_row.append(other_index)

                if self._is_same_column(current.bounds, other.bounds):
                    same_column.append(other_index)

                if other.bounds.right <= current.bounds.x:
                    left.append(neighbor)

                elif other.bounds.x >= current.bounds.right:
                    right.append(neighbor)

                elif other.bounds.bottom <= current.bounds.y:
                    above.append(neighbor)

                elif other.bounds.y >= current.bounds.bottom:
                    below.append(neighbor)

            contexts.append(
                LogicalObjectContext(
                    object_index=index,
                    left=tuple(self._sort_neighbors(left)),
                    right=tuple(self._sort_neighbors(right)),
                    above=tuple(self._sort_neighbors(above)),
                    below=tuple(self._sort_neighbors(below)),
                    same_row=tuple(sorted(same_row)),
                    same_column=tuple(sorted(same_column)),
                )
            )

        return tuple(contexts)

    def _relation(self, index, current, other_index, other):
        del index, other_index

        x_overlap = self._overlap_ratio(
            current.x,
            current.right,
            other.x,
            other.right,
        )
        y_overlap = self._overlap_ratio(
            current.y,
            current.bottom,
            other.y,
            other.bottom,
        )

        horizontal_gap = self._gap(
            current.x,
            current.right,
            other.x,
            other.right,
        )
        vertical_gap = self._gap(
            current.y,
            current.bottom,
            other.y,
            other.bottom,
        )

        current_center_x, current_center_y = current.center
        other_center_x, other_center_y = other.center

        center_distance = hypot(
            current_center_x - other_center_x,
            current_center_y - other_center_y,
        )

        if (
            other.right <= current.x
            and (
                y_overlap >= self.overlap_tolerance
                or self._is_same_row(current, other)
            )
        ):
            return horizontal_gap, vertical_gap, x_overlap, y_overlap, center_distance

        if (
            other.x >= current.right
            and (
                y_overlap >= self.overlap_tolerance
                or self._is_same_row(current, other)
            )
        ):
            return horizontal_gap, vertical_gap, x_overlap, y_overlap, center_distance

        if (
            other.bottom <= current.y
            and (
                x_overlap >= self.overlap_tolerance
                or self._is_same_column(current, other)
            )
        ):
            return horizontal_gap, vertical_gap, x_overlap, y_overlap, center_distance

        if (
            other.y >= current.bottom
            and (
                x_overlap >= self.overlap_tolerance
                or self._is_same_column(current, other)
            )
        ):
            return horizontal_gap, vertical_gap, x_overlap, y_overlap, center_distance

        return None

    def _is_same_row(self, current, other) -> bool:
        _, current_center_y = current.center
        _, other_center_y = other.center

        vertical_center_delta = abs(current_center_y - other_center_y)
        tolerance = max(
            current.height,
            other.height,
        ) * self.row_vertical_tolerance

        if vertical_center_delta > tolerance:
            return False

        horizontal_gap = self._gap(
            current.x,
            current.right,
            other.x,
            other.right,
        )

        max_width = max(current.width, other.width)

        return horizontal_gap <= max_width * 3

    def _is_same_column(self, current, other) -> bool:
        current_center_x, _ = current.center
        other_center_x, _ = other.center

        horizontal_center_delta = abs(current_center_x - other_center_x)
        tolerance = max(
            current.width,
            other.width,
        ) * self.column_horizontal_tolerance

        if horizontal_center_delta > tolerance:
            return False

        vertical_gap = self._gap(
            current.y,
            current.bottom,
            other.y,
            other.bottom,
        )

        max_height = max(current.height, other.height)

        return vertical_gap <= max_height * 3

    @staticmethod
    def _overlap_ratio(start_a, end_a, start_b, end_b) -> float:
        overlap = max(0, min(end_a, end_b) - max(start_a, start_b))

        length_a = max(1, end_a - start_a)
        length_b = max(1, end_b - start_b)

        return overlap / min(length_a, length_b)

    @staticmethod
    def _gap(start_a, end_a, start_b, end_b) -> int:
        if end_a < start_b:
            return start_b - end_a

        if end_b < start_a:
            return start_a - end_b

        return 0

    @staticmethod
    def _sort_neighbors(
        neighbors: list[LogicalObjectNeighbor],
    ) -> list[LogicalObjectNeighbor]:
        return sorted(
            neighbors,
            key=lambda item: (
                item.horizontal_gap + item.vertical_gap,
                item.center_distance,
            ),
        )
