from dataclasses import (
    dataclass,
    field
)


@dataclass
class VisionTask:

    name: str

    goals: list = field(

        default_factory=list

    )