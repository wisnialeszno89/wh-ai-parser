class OpeningAliases:

    def normalize(

        self,

        text

    ):

        replacements = {

            "RU + FIX": "RU|FIX",

            "RU+FIX": "RU|FIX",

            "RU FIX": "RU|FIX",

            "R+F": "RU|FIX",

            "RU/FIX": "RU|FIX",

            "RU | FIX": "RU|FIX",

            "RU  FIX": "RU|FIX"

        }

        for source, target in replacements.items():

            text = text.replace(

                source,

                target

            )

        return text