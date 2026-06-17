from app.wh.runtime.query.query_model import (
    QueryModel
)


class QueryParser:

    def parse(

        self,

        text

    ):

        lines = [

            line.strip()

            for line in text.splitlines()

            if line.strip()

        ]

        size = lines[0]

        pattern = lines[1]

        profile = lines[2]

        glass = lines[3]

        width, height = (

            size.split(

                "x"

            )

        )

        return QueryModel(

            width=int(

                width

            ),

            height=int(

                height

            ),

            pattern=pattern,

            profile=profile,

            glass=glass

        )