from app.wh.runtime.features.profile_package import (
    ProfilePackage
)

from app.wh.runtime.profile_registry import (
    PROFILES
)


class ProfileParser:

    def parse(

        self,

        text

    ):

        lower = (

            text.lower()

        )

        profile = (

            ProfilePackage()

        )

        for alias, data in (

            PROFILES.items()

        ):

            if alias in lower:

                profile.manufacturer = (

                    data[0]

                )

                profile.system = (

                    data[1]

                )

                break

        return profile