from dataclasses import dataclass


@dataclass
class MatchResult:

    x: int

    y: int

    width: int

    height: int

    confidence: float

    @property
    def center_x(

        self

    ):

        return (

            self.x +

            self.width // 2

        )

    @property
    def center_y(

        self

    ):

        return (

            self.y +

            self.height // 2

        )