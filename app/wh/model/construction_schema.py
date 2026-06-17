from dataclasses import (
    dataclass,
    field
)

from app.wh.model.row import (
    Row
)

from app.wh.model.addon import (
    Addon
)


@dataclass
class ConstructionSchema:

    category: str

    width_mm: int

    height_mm: int

    rows: list[Row] = field(

        default_factory=list

    )

    addons: list[Addon] = field(

        default_factory=list

    )