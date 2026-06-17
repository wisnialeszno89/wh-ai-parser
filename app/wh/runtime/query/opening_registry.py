class OpeningRegistry:

    def __init__(

        self

    ):

        self.aliases = {

            "RU|FIX": [

                "RU|FIX",

                "RU+FIX",

                "RU FIX",

                "RU/FIX",

                "R+F"

            ]

        }

    def resolve(

        self,

        text

    ):

        text = text.upper()

        for canonical, aliases in (

            self.aliases.items()

        ):

            if text in aliases:

                return canonical

        return text