from app.wh.runtime.vision.retry_policy import (
    RetryPolicy
)


def test_retry_policy():

    policy = (

        RetryPolicy()

    )

    assert (

        policy.max_attempts

        ==

        3

    )