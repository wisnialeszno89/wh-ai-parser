from app.wh.model.opening import (
    Opening
)


class ConstructionNotation:

    def describe(

        self,

        construction

    ):

        mapping = {

            Opening.FIX:

            "FIX",

            Opening.TURN:

            "R",

            Opening.TILT:

            "U",

            Opening.TILT_TURN:

            "RU",

            Opening.PSK:

            "PSK",

            Opening.HST:

            "HST"

        }

        names = []

        for segment in (

            construction.segments

        ):

            names.append(

                mapping[

                    segment.opening

                ]

            )

        return "+".join(

            names

        )