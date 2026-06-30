class ProfileResolver:

    PROFILES = {

        "veka 82": "VEKA_82",

        "softline 82": "VEKA_82",

        "v82": "VEKA_82"

    }

    def resolve(
        self,
        text: str
    ):

        text = text.lower()

        for alias, profile in self.PROFILES.items():

            if alias in text:

                return profile

        return None