from enum import (
    Enum
)


class PredictionStrategy(

    Enum

):

    NORMAL = (

        "normal"

    )

    EXTRA_LOGGING = (

        "extra_logging"

    )

    SAFE_MODE = (

        "safe_mode"

    )

    REQUIRE_HUMAN_REVIEW = (

        "require_human_review"

    )