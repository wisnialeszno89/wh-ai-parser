from app.wh.runtime.vision.alternative_strategy import (
    AlternativeStrategy
)


class AlternativeStrategyEngine:

    def choose(

        self,

        reason

    ):

        if (

            reason

            ==

            "template_not_found"

        ):

            return (

                AlternativeStrategy.OCR_FALLBACK

            )

        if (

            reason

            ==

            "checkbox_failed"

        ):

            return (

                AlternativeStrategy.CLICK_BY_COORDINATES

            )

        if (

            reason

            ==

            "dropdown_failed"

        ):

            return (

                AlternativeStrategy.TYPE_TEXT

            )

        return (

            AlternativeStrategy.RETRY_SAME

        )