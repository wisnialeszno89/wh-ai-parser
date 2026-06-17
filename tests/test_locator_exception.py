from app.runtime.locator_exception import (
    LocatorException
)


def test_locator_exception():

    error = LocatorException(

        "profile not found"

    )

    assert str(

        error

    ) == "profile not found"