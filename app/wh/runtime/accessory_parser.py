from app.wh.runtime.features.accessory_package import (
    AccessoryPackage
)

from app.wh.runtime.accessory_registry import (
    ROLLER_SHUTTERS,
    SILLS,
    MOSQUITO_NET_ALIASES,
    CONNECTOR_ALIASES,
    EXTENSIONS
)


class AccessoryParser:

    def parse(

        self,

        text

    ):

        lower = (

            text.lower()

        )

        accessories = (

            AccessoryPackage()

        )

        for alias, value in (

            ROLLER_SHUTTERS.items()

        ):

            if alias in lower:

                accessories.roller_shutter = (

                    value

                )

                break

        for alias, value in (

            SILLS.items()

        ):

            if alias in lower:

                accessories.sill = (

                    value

                )

                break

        accessories.mosquito_net = any(

            alias in lower

            for alias in MOSQUITO_NET_ALIASES

        )

        accessories.connector = any(

            alias in lower

            for alias in CONNECTOR_ALIASES

        )

        for alias, value in (

            EXTENSIONS.items()

        ):

            if alias in lower:

                accessories.extension_mm = (

                    value

                )

                break

        return accessories