from app.wh.runtime.vision.meta_cognition_insight import (
    MetaCognitionInsight
)


class MetaCognitionEngine:

    def analyze(

        self,

        brain

    ):

        total_successes = 0

        total_failures = 0

        for reflection in (

            brain.reflection_memory.reflections

        ):

            if reflection.success:

                total_successes += 1

            else:

                total_failures += 1

        total = (

            total_successes

            +

            total_failures

        )

        if total == 0:

            success_rate = 0.0

        else:

            success_rate = (

                total_successes

                /

                total

            )

        return (

            MetaCognitionInsight(

                total_reflections=total,

                total_successes=total_successes,

                total_failures=total_failures,

                success_rate=success_rate

            )

        )