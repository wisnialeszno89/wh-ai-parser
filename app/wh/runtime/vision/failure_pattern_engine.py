from collections import (
    Counter
)

from app.wh.runtime.vision.failure_pattern import (
    FailurePattern
)

from app.wh.runtime.vision.failure_pattern_result import (
    FailurePatternResult
)


class FailurePatternEngine:

    def analyze(

        self,

        failed_patterns

    ):

        counter = (

            Counter(

                failed_patterns

            )

        )

        patterns = []

        for pattern, count in (

            counter.items()

        ):

            patterns.append(

                FailurePattern(

                    pattern=pattern,

                    failures=count

                )

            )

        patterns.sort(

            key=lambda x: x.failures,

            reverse=True

        )

        return (

            FailurePatternResult(

                patterns=patterns

            )

        )