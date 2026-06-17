class ProfileAliases:

    def normalize(

        self,

        text

    ):

        replacements = {

            "VEKA82": "VEKA SOFTLINE 82",

            "SL82": "VEKA SOFTLINE 82",

            "SOFTLINE82": "VEKA SOFTLINE 82",

            "VEKA SOFTLINE82": "VEKA SOFTLINE 82"

        }

        for source, target in replacements.items():

            text = text.replace(

                source,

                target

            )

        return text