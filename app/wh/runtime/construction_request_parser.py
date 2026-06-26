from app.wh.runtime.construction_request import (
    ConstructionRequest
)


class ConstructionRequestParser:

    def parse(

        self,

        text

    ):

        lines = [

            line.strip()

            for line in text.splitlines()

            if line.strip()

        ]

        first_line = (

            lines[0]

        )

        parts = (

            first_line.split()

        )

        size = (

            parts[0]

        )

        notation = (

            " ".join(

                parts[1:]

            )

            .upper()

        )

        width, height = (

            size.lower().split(

                "x"

            )

        )

        return ConstructionRequest(

            width=int(

                width

            ),

            height=int(

                height

            ),

            notation=notation

        )