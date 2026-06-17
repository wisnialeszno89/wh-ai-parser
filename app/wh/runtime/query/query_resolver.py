from app.wh.runtime.query.dimension_parser import (
    DimensionParser
)

from app.wh.runtime.query.opening_registry import (
    OpeningRegistry
)

from app.wh.runtime.query.profile_registry import (
    ProfileRegistry
)

from app.wh.runtime.query.glass_registry import (
    GlassRegistry
)

from app.wh.runtime.query.query_model import (
    QueryModel
)


class QueryResolver:

    def __init__(

        self

    ):

        self.dimension_parser = (

            DimensionParser()

        )

        self.opening_registry = (

            OpeningRegistry()

        )

        self.profile_registry = (

            ProfileRegistry()

        )

        self.glass_registry = (

            GlassRegistry()

        )

    def resolve(

        self,

        text

    ):

        width, height = (

            self.dimension_parser.parse(

                text

            )

        )

        lines = [

            line.strip().upper()

            for line in text.splitlines()

            if line.strip()

        ]

        pattern = (

            self.opening_registry.resolve(

                lines[1]

            )

        )

        profile = (

            self.profile_registry.resolve(

                lines[2]

            )

        )

        glass = (

            self.glass_registry.resolve(

                lines[3]

            )

        )

        return QueryModel(

            width=width,

            height=height,

            pattern=pattern,

            profile=profile,

            glass=glass

        )