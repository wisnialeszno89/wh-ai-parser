class PatternParser:

    def parse(

        self,

        pattern

    ):

        rows = []

        for row in pattern.split(

            "/"

        ):

            rows.append(

                row.split(

                    "|"

                )

            )

        return rows