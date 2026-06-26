from app.wh.runtime.features.glass_package import (
    GlassPackage
)

from app.wh.runtime.glass_registry import (
    GLASS_TYPES,
    GLASS_PACKAGES,
    WARM_EDGE_ALIASES,
    SWISSPACER_ALIASES,
    P4_ALIASES
)


class GlassParser:

    def parse(

        self,

        text

    ):

        lower = (

            text.lower()

        )

        glass = (

            GlassPackage()

        )

        for alias, value in (

            GLASS_TYPES.items()

        ):

            if alias in lower:

                glass.type = value

                break

        for alias, value in (

            GLASS_PACKAGES.items()

        ):

            if alias in lower:

                glass.thickness_mm = value

                break

        glass.warm_edge = any(

            alias in lower

            for alias in WARM_EDGE_ALIASES

        )

        glass.swisspacer = any(

            alias in lower

            for alias in SWISSPACER_ALIASES

        )

        glass.security_p4 = any(

            alias in lower

            for alias in P4_ALIASES

        )

        return glass