from app.wh.runtime.construction_schema import (
    ConstructionSchema
)

from app.wh.runtime.segments.segment import (
    Segment
)

from app.wh.model.opening import (
    Opening
)


class ConstructionParser:

    def parse(

        self,

        text

    ):

        mapping = {

            "FIX": Opening.FIX,

            "R": Opening.TURN,

            "U": Opening.TILT,

            "RU": Opening.TILT_TURN,

            "PSK": Opening.PSK,

            "HST": Opening.HST

        }

        segments = []

        for token in text.split(

            "+"

        ):

            segments.append(

                Segment(

                    opening=

                    mapping[

                        token

                    ]

                )

            )

        return ConstructionSchema(

            width=0,

            height=0,

            schema=text,

            segments=segments

        )