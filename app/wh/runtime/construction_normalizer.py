class ConstructionNormalizer:

    def normalize(

        self,

        text

    ):

        text = (

            text.upper()

        )

        separators = [

            " ",

            "/",

            ","

        ]

        for separator in separators:

            text = (

                text.replace(

                    separator,

                    "+"

                )

            )

        while "++" in text:

            text = (

                text.replace(

                    "++",

                    "+"

                )

            )

        return (

            text.strip(

                "+"

            )

        )