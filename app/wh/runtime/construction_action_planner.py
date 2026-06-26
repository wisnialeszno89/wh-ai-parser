from app.wh.runtime.segment_action_planner import (
    SegmentActionPlanner
)


class ConstructionActionPlanner:

    def __init__(

        self

    ):

        self.segment_planner = (

            SegmentActionPlanner()

        )

    def plan(

        self,

        construction

    ):

        actions = []

        for segment in (

            construction.segments

        ):

            actions.extend(

                self.segment_planner.plan(

                    segment.opening

                )

            )

        return actions