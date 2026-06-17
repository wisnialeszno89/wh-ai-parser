from app.wh.vision.locator_exception import (
    LocatorException
)


def test_locator_exception_v2():

    error = LocatorException(

        "profile not found"

    )

    assert str(

        error

    ) == "profile not found"