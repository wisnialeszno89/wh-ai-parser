from app.wh.runtime.runtime_tool import (
    RuntimeTool
)

from app.wh.runtime.constructions.base_builder import (
    BaseBuilder
)

from app.wh.runtime.constructions.segments.segment_layout import (
    SegmentLayout
)

from app.wh.runtime.constructions.segments.segment_geometry import (
    SegmentGeometry
)

from app.wh.runtime.constructions.executors.executor_registry import (
    ExecutorRegistry
)


class FixRuBuilder(

    BaseBuilder
):

    def build(

        self,
        runtime,
        intent
    ):

        print(
            "[BUILDER] FIX_RU"
        )

        layout = (
            SegmentLayout.fix_ru()
        )

        runtime.select_tool(
            RuntimeTool.GLASS
        )

        positions = (
            SegmentGeometry.calculate_positions(

                runtime.session.canvas_bounds,

                layout
            )
        )

        center_y = (

            runtime.session.canvas_bounds[1] +

            runtime.session.canvas_bounds[3]

        ) // 2

        for index, segment in enumerate(
            layout
        ):

            x = positions[index]

            print(
                f"[SEGMENT] "
                f"{segment.kind.value} "
                f"-> x={x}"
            )

            executor = (
                ExecutorRegistry.resolve(
                    segment.kind
                )
            )

            executor.execute(

                runtime,

                x,

                center_y,

                segment
            )