from dataclasses import (
    dataclass
)

from app.wh.runtime.fields.field import (
    Field
)


@dataclass
class Transom:

    top_field: Field

    bottom_field: Field