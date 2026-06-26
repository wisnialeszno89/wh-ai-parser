from app.wh.runtime.vision.confidence_adaptive_mode_decision import (
    ConfidenceAdaptiveModeDecision
)

from app.wh.runtime.vision.confidence_level import (
    ConfidenceLevel
)

from app.wh.runtime.vision.adaptive_execution_mode import (
    AdaptiveExecutionMode
)


class ConfidenceAdaptiveModeEngine:

    def decide(

        self,

        confidence_decision

    ):

        if (

            confidence_decision.level

            ==

            ConfidenceLevel.VERY_HIGH

        ):

            mode = (

                AdaptiveExecutionMode.NORMAL

            )

        elif (

            confidence_decision.level

            ==

            ConfidenceLevel.HIGH

        ):

            mode = (

                AdaptiveExecutionMode.CAREFUL_MODE

            )

        elif (

            confidence_decision.level

            ==

            ConfidenceLevel.MEDIUM

        ):

            mode = (

                AdaptiveExecutionMode.SAFE_MODE

            )

        else:

            mode = (

                AdaptiveExecutionMode.HUMAN_REVIEW_MODE

            )

        return (

            ConfidenceAdaptiveModeDecision(

                level=confidence_decision.level,

                mode=mode

            )

        )