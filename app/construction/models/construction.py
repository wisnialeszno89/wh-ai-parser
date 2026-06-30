from dataclasses import dataclass, field

from app.construction.models.field import (
    Field
)


@dataclass
class Construction:

    fields: list[Field] = field(
        default_factory=list
    )

    width: int | None = None

    height: int | None = None

    def add_field(
        self,
        field: Field
    ):

        self.fields.append(
            field
        )