from collections import (
    Counter
)

from app.wh.runtime.vision.success_pattern import (
    SuccessPattern
)

from app.wh.runtime.vision.success_pattern_result import (
    SuccessPatternResult
)


class SuccessPatternEngine:

    def analyze(

        self,

        successful_patterns

    ):

        counter = (

            Counter(

                successful_patterns

            )

        )

        patterns = []

        for pattern, count in (

            counter.items()

        ):

            patterns.append(

                SuccessPattern(

                    pattern=pattern,

                    successes=count

                )

            )

        patterns.sort(

            key=lambda x: x.successes,

            reverse=True

        )

        return (

            SuccessPatternResult(

                patterns=patterns

            )

        )