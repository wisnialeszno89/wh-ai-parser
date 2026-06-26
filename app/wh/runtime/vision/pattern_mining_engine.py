from collections import (
    Counter
)

from app.wh.runtime.vision.pattern_frequency import (
    PatternFrequency
)

from app.wh.runtime.vision.pattern_mining_result import (
    PatternMiningResult
)


class PatternMiningEngine:

    def analyze(

        self,

        patterns

    ):

        counter = (

            Counter(

                patterns

            )

        )

        result = []

        for pattern, count in (

            counter.items()

        ):

            result.append(

                PatternFrequency(

                    pattern=pattern,

                    count=count

                )

            )

        result.sort(

            key=lambda x: x.count,

            reverse=True

        )

        return (

            PatternMiningResult(

                patterns=result

            )

        )