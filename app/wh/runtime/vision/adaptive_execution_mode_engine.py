from app.wh.runtime.vision.prediction_strategy import (
    PredictionStrategy
)

from app.wh.runtime.vision.adaptive_execution_mode import (
    AdaptiveExecutionMode
)


class AdaptiveExecutionModeEngine:

    def decide(

        self,

        strategy

    ):

        if (

            strategy

            ==

            PredictionStrategy.NORMAL

        ):

            return (

                AdaptiveExecutionMode.NORMAL

            )

        if (

            strategy

            ==

            PredictionStrategy.EXTRA_LOGGING

        ):

            return (

                AdaptiveExecutionMode.CAREFUL_MODE

            )

        if (

            strategy

            ==

            PredictionStrategy.SAFE_MODE

        ):

            return (

                AdaptiveExecutionMode.SAFE_MODE

            )

        return (

            AdaptiveExecutionMode.HUMAN_REVIEW_MODE

        )