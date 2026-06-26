from app.wh.runtime.features.security_package import (
    SecurityPackage
)

from app.wh.runtime.security_registry import (
    RC_ALIASES,
    CONTACT_ALIASES
)


class SecurityParser:

    def parse(

        self,

        text

    ):

        lower = (

            text.lower()

        )

        security = (

            SecurityPackage()

        )

        for alias in (

            RC_ALIASES

        ):

            if alias in lower:

                security.rc2 = True

                break

        security.contacts = any(

            alias in lower

            for alias in CONTACT_ALIASES

        )

        return security