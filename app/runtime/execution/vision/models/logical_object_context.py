from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LogicalObjectNeighbor:
    object_index: int
    horizontal_gap: int
    vertical_gap: int
    x_overlap_ratio: float
    y_overlap_ratio: float
    center_distance: float


@dataclass(frozen=True, slots=True)
class LogicalObjectContext:
    object_index: int
    left: tuple[LogicalObjectNeighbor, ...] = ()
    right: tuple[LogicalObjectNeighbor, ...] = ()
    above: tuple[LogicalObjectNeighbor, ...] = ()
    below: tuple[LogicalObjectNeighbor, ...] = ()
    same_row: tuple[int, ...] = ()
    same_column: tuple[int, ...] = ()

    @property
    def nearest_neighbor(self) -> LogicalObjectNeighbor | None:
        neighbors = self.left + self.right + self.above + self.below
        if not neighbors:
            return None
        return min(neighbors, key=lambda item: item.center_distance)
