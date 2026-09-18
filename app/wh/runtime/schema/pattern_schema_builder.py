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


class PatternSchemaBuilder:

    def build(

        self,

        rows,

        width,

        height,

        openings=None

    ):

        mapping = {

            "RU": TILT_TURN,

            "FIX": FIX

        }

        segments = []

        if openings is None:
            openings = []

        cols = len(

            rows[0]

        )

        ratio_x = []

        ratio_y = []

        if cols > 1:

            step_x = 1 / cols

            ratio_x = [

                round(

                    step_x * i,

                    2

                )

                for i in range(

                    1,

                    cols

                )

            ]

        if len(

            rows

        ) > 1:

            step_y = 1 / len(

                rows

            )

            ratio_y = [

                round(

                    step_y * i,

                    2

                )

                for i in range(

                    1,

                    len(

                        rows

                    )

                )

            ]

        opening_index = 0

        for row in rows:

            for token in row:

                direction = "NONE"

                if opening_index < len(openings):

                    opening_code = openings[opening_index]

                    if opening_code == "RIGHT_TILT_TURN":

                        direction = "RIGHT"

                    elif opening_code == "LEFT_TILT_TURN":

                        direction = "LEFT"

                segments.append(

                    Segment(

                        opening=mapping[

                            token

                        ],

                        direction=direction

                    )

                )

                opening_index += 1

        return ConstructionSchema(

            width=width,

            height=height,

            schema="pattern",

            ratio_x=ratio_x,

            ratio_y=ratio_y,

            segments=segments

        )