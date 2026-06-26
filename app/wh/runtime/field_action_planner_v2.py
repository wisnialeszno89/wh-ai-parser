from app.wh.runtime.segment_action_planner import (
    SegmentActionPlanner
)


class FieldActionPlannerV2:

    def __init__(

        self

    ):

        self.segment_planner = (

            SegmentActionPlanner()

        )

    def plan(

        self,

        regions

    ):

        for region in regions:

            region.actions = (

                self.segment_planner.plan(

                    region.opening

                )

            )

        return regions