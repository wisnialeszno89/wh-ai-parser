from enum import (
    Enum
)


class FailureAction(

    Enum

):

    RETRY = (

        "retry"

    )

    RECOVER = (

        "recover"

    )

    HUMAN_REVIEW = (

        "human_review"

    )

    PARTIAL_SUCCESS = (

        "partial_success"

    )