from dataclasses import (
    dataclass
)

from app.wh.runtime.fields.field import (
    Field
)


@dataclass
class Mullion:

    left_field: Field

    right_field: Field