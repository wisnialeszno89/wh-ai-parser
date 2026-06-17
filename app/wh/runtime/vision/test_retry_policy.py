from unittest.mock import (
    MagicMock
)

from app.wh.runtime.vision.retry_policy import (
    RetryPolicy
)


def test_retry_policy():

    counter = {

        "value": 0

    }

    def callback():

        counter["value"] += 1

        return (

            counter["value"]

            == 3

        )

    policy = (

        RetryPolicy()

    )

    policy.wait_agent = (

        MagicMock()

    )

    result = (

        policy.execute(

            callback,

            attempts=3,

            delay=0

        )

    )

    assert result is True

    assert counter["value"] == 3

    assert (

        policy.wait_agent.wait.call_count

        == 2

    )