from app.wh.runtime.construction_schema import (
    ConstructionSchema
)

from app.wh.runtime.segments.segment import (
    Segment
)

from app.wh.runtime.openings.opening_types import (
    TILT_TURN,
    FIX
)


class ConstructionSchemaFactory:

    def create(

        self,

        pattern,

        width,

        height

    ):

        mapping = {

            "RU": TILT_TURN,

            "FIX": FIX

        }

        tokens = pattern.split(

            "|"

        )

        segments = []

        for token in tokens:

            segments.append(

                Segment(

                    opening=mapping[

                        token

                    ]

                )

            )

        ratio_x = []

        if len(

            segments

        ) > 1:

            step = 1 / len(

                segments

            )

            ratio_x = [

                round(

                    step * i,

                    2

                )

                for i in range(

                    1,

                    len(

                        segments

                    )

                )

            ]

        return ConstructionSchema(

            width=width,

            height=height,

            schema=pattern,

            ratio_x=ratio_x,

            segments=segments

        )