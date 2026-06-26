from app.wh.runtime.features.security_package import (
    SecurityPackage
)


def test_security_package():

    package = (

        SecurityPackage(

            rc2=True,

            contacts=True

        )

    )

    assert package.rc2 is True

    assert package.contacts is True