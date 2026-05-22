from app.wh.runtime.constructions.executors.fix_executor import (
    FixExecutor
)

from app.wh.runtime.constructions.executors.ru_executor import (
    RuExecutor
)

from app.wh.runtime.constructions.segments.segment_kind import (
    SegmentKind
)


class ExecutorRegistry:

    @staticmethod
    def resolve(

        segment_kind
    ):

        mapping = {

            SegmentKind.FIX:

                FixExecutor(),

            SegmentKind.RU:

                RuExecutor()
        }

        if segment_kind not in mapping:

            raise RuntimeError(

                f"Missing executor: "
                f"{segment_kind}"
            )

        return mapping[
            segment_kind
        ]