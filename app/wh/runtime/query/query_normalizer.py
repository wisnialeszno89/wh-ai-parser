from app.wh.runtime.query.opening_aliases import (
    OpeningAliases
)

from app.wh.runtime.query.profile_aliases import (
    ProfileAliases
)

from app.wh.runtime.query.glass_aliases import (
    GlassAliases
)


class QueryNormalizer:

    def __init__(

        self

    ):

        self.opening_aliases = (

            OpeningAliases()

        )

        self.profile_aliases = (

            ProfileAliases()

        )

        self.glass_aliases = (

            GlassAliases()

        )

    def normalize(

        self,

        text

    ):

        text = text.upper()

        text = text.replace(

            " X ",

            "x"

        )

        text = (

            self.opening_aliases.normalize(

                text

            )

        )

        text = (

            self.profile_aliases.normalize(

                text

            )

        )

        text = (

            self.glass_aliases.normalize(

                text

            )

        )

        return text