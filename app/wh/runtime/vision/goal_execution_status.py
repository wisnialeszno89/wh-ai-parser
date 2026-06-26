from enum import (
    Enum
)


class GoalExecutionStatus(

    Enum

):

    SUCCESS = (

        "success"

    )

    FAILED = (

        "failed"

    )

    PARTIAL_SUCCESS = (

        "partial_success"

    )

    SKIPPED = (

        "skipped"

    )

    HUMAN_REVIEW = (

        "human_review"

    )