from enum import (
    Enum
)


class PredictionRiskLevel(

    Enum

):

    SAFE = (

        "safe"

    )

    WARNING = (

        "warning"

    )

    HIGH_RISK = (

        "high_risk"

    )

    CRITICAL = (

        "critical"

    )