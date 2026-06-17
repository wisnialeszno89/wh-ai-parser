from app.runtime.retry_policy import (
    RetryPolicy
)


def test_retry_policy():

    policy = RetryPolicy()

    assert (

        policy.max_retries

        ==

        3

    )