class Translator:

    def translate(

        self,

        construction

    ):

        if construction.schema == "basic_window":

            return [

                "frame",

                "sash",

                "glass"

            ]

        if construction.schema == "fix_window":

            return [

                "frame",

                "glass"

            ]

        raise Exception(

            f"Unknown schema: {construction.schema}"

        )