from app.wh.runtime.runtime_mode import (
    RuntimeMode
)


def test_runtime_mode():

    assert (

        RuntimeMode.FAKE

        ==

        "FAKE"

    )

    assert (

        RuntimeMode.REAL

        ==

        "REAL"

    )