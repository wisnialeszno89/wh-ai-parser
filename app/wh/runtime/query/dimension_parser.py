import re


class DimensionParser:

    def parse(

        self,

        text

    ):

        text = text.upper()

        text = text.replace(

            " NA ",

            "X"

        )

        pattern = r"(\d+)\s*[X]\s*(\d+)"

        match = re.search(

            pattern,

            text

        )

        if not match:

            raise Exception(

                "Dimensions not found"

            )

        width = int(

            match.group(

                1

            )

        )

        height = int(

            match.group(

                2

            )

        )

        return width, height