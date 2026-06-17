class GlassRegistry:

    def __init__(

        self

    ):

        self.aliases = {

            "3 SZYBY": [

                "3 SZYBY",

                "3SZYBY",

                "TRZYSZYBOWE",

                "PAKIET 3 SZYBY",

                "PAKIET TRZYSZYBOWY"

            ],

            "2 SZYBY": [

                "2 SZYBY",

                "2SZYBY",

                "DWUSZYBOWE"

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