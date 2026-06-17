class ProfileRegistry:

    def __init__(

        self

    ):

        self.aliases = {

            "VEKA SOFTLINE 82": [

                "VEKA82",

                "SL82",

                "SOFTLINE82",

                "VEKA SOFTLINE82",

                "VEKA SOFTLINE 82"

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