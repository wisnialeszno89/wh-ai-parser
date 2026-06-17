from app.wh.runtime.action import (
    Action
)


class ActionPlanner:

    def plan(

        self,

        construction

    ):

        actions = []

        for segment in construction.segments:

            actions.append(

                Action(

                    segment.kind,

                    f"{segment.kind}_button.png"

                )

            )

        return actions