from enum import (
    Enum
)


class AdaptiveExecutionMode(

    Enum

):

    NORMAL = (

        "normal"

    )

    SAFE_MODE = (

        "safe_mode"

    )

    CAREFUL_MODE = (

        "careful_mode"

    )

    RECOVERY_MODE = (

        "recovery_mode"

    )

    HUMAN_REVIEW_MODE = (

        "human_review_mode"

    )