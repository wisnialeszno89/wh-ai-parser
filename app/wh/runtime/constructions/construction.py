from dataclasses import (
    dataclass,
    field
)


@dataclass
class Construction:

    fields: list = field(

        default_factory=list

    )

    mullions: list = field(

        default_factory=list

    )

    transoms: list = field(

        default_factory=list

    )