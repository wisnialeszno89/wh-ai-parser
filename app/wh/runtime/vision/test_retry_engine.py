from app.wh.runtime.vision.retry_engine import (
    RetryEngine
)


def test_retry_engine():

    engine = (

        RetryEngine()

    )

    attempts = [

        False,

        False,

        True

    ]

    def func():

        return (

            attempts.pop(

                0

            )

        )

    result = (

        engine.execute(

            func,

            retry_count=3

        )

    )

    assert (

        result

        is True

    )