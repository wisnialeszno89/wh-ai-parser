from dataclasses import (
    dataclass,
    field
)


@dataclass
class Field:

    id: int

    x: int

    y: int

    opening: str = ""

    actions: list = field(

        default_factory=list

    )

    context: object = None

    def left(

        self

    ):

        if self.context:

            return self.context.left()

        return None

    def right(

        self

    ):

        if self.context:

            return self.context.right()

        return None

    def top(

        self

    ):

        if self.context:

            return self.context.top()

        return None

    def bottom(

        self

    ):

        if self.context:

            return self.context.bottom()

        return None