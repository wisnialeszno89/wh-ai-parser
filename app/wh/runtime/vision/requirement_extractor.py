import re

from app.wh.runtime.vision.offer_requirements import (
    OfferRequirements
)


class RequirementExtractor:

    def extract(

        self,

        text: str

    ) -> OfferRequirements:

        lower = text.lower()

        requirements = OfferRequirements()

        windows = re.search(

            r"(\d+)\s+windows?",

            lower

        )

        if windows:

            requirements.windows = int(

                windows.group(

                    1

                )

            )

        balcony = re.search(

            r"(\d+)\s+balcony\s+doors?",

            lower

        )

        if balcony:

            requirements.balcony_doors = int(

                balcony.group(

                    1

                )

            )

        if "anthracite" in lower:

            requirements.outside_color = "Anthracite"

        if "white" in lower:

            requirements.inside_color = "White"

        if "triple" in lower:

            requirements.glazing = "Triple"

        if "rc2" in lower:

            requirements.security = "RC2"

        return requirements