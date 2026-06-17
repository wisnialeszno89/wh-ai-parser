from app.wh.runtime.openings.opening_types import (
    TILT_TURN,
    TURN_ONLY,
    FIX
)


class OpeningTypeEngine:

    def resolve(

        self,

        opening

    ):

        mapping = {

            TILT_TURN: [

                "frame",

                "sash",

                "glass"

            ],

            TURN_ONLY: [

                "frame",

                "sash",

                "glass"

            ],

            FIX: [

                "frame",

                "glass"

            ]

        }

        if opening not in mapping:

            raise Exception(

                f"Unknown opening type: {opening}"

            )

        return mapping[

            opening

        ]