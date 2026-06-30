class ColorResolver:

    COLORS = {

        "antracyt obustronny":
            "7016_BOTH",

        "antracyt":
            "7016",

        "złoty dąb":
            "GOLDEN_OAK"
    }

    def resolve(self, text):

        text = text.lower()

        for alias, color in self.COLORS.items():

            if alias in text:

                return color

        return None