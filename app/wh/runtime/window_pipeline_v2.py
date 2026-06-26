from app.wh.runtime.field_map_builder import (
    FieldMapBuilder
)

from app.wh.runtime.field_classifier import (
    FieldClassifier
)

from app.wh.runtime.field_region_builder import (
    FieldRegionBuilder
)

from app.wh.runtime.field_action_planner_v2 import (
    FieldActionPlannerV2
)

from app.wh.runtime.field_executor_v2 import (
    FieldExecutorV2
)


class WindowPipelineV2:

    def __init__(

        self

    ):

        self.map_builder = (

            FieldMapBuilder()

        )

        self.classifier = (

            FieldClassifier()

        )

        self.region_builder = (

            FieldRegionBuilder()

        )

        self.planner = (

            FieldActionPlannerV2()

        )

        self.executor = (

            FieldExecutorV2()

        )

    def execute(

        self,

        grid,

        schema

    ):

        fields = (

            self.map_builder.build(

                grid

            )

        )

        fields = (

            self.classifier.classify(

                fields,

                schema

            )

        )

        regions = (

            self.region_builder.build(

                fields

            )

        )

        regions = (

            self.planner.plan(

                regions

            )

        )

        return (

            self.executor.execute(

                regions

            )

        )