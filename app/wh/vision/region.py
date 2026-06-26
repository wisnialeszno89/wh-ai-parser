from dataclasses import (
    dataclass
)


@dataclass
class Region:

    left: int

    top: int

    right: int

    bottom: int

    @property
    def width(

        self

    ):

        return self.right - self.left

    @property
    def height(

        self

    ):

        return self.bottom - self.top

    @property
    def center_x(

        self

    ):

        return (

            self.left +

            self.right

        ) // 2

    @property
    def center_y(

        self

    ):

        return (

            self.top +

            self.bottom

        ) // 2