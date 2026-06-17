class GlassAliases:

    def normalize(

        self,

        text

    ):

        replacements = {

            "3SZYBY": "3 SZYBY",

            "PAKIET 3 SZYBY": "3 SZYBY",

            "TRZYSZYBOWE": "3 SZYBY",

            "TRZY SZYBY": "3 SZYBY",

            "PAKIET TRZYSZYBOWY": "3 SZYBY",

            "DWUSZYBOWE": "2 SZYBY",

            "2SZYBY": "2 SZYBY"

        }

        for source, target in replacements.items():

            text = text.replace(

                source,

                target

            )

        return text