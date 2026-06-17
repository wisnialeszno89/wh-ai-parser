from app.wh.runtime.gui_action import (
    GUIAction
)

from app.wh.runtime.gui_plan import (
    GUIPlan
)

from app.wh.runtime.opening_strategy_factory import (
    OpeningStrategyFactory
)


class ActionPlannerV2:

    def __init__(

        self

    ):

        self.factory = (

            OpeningStrategyFactory()

        )

    def plan(

        self,

        construction

    ):

        actions = [

            GUIAction(

                name="frame"

            )

        ]

        for row_index, row in enumerate(

            construction.rows

        ):

            if row_index > 0:

                actions.append(

                    GUIAction(

                        name="add_horizontal"

                    )

                )

            for segment_index, segment in enumerate(

                row.segments

            ):

                if segment_index > 0:

                    actions.append(

                        GUIAction(

                            name="add_vertical"

                        )

                    )

                strategy = (

                    self.factory.create(

                        segment.opening

                    )

                )

                actions.extend(

                    strategy.plan()

                )

        actions.append(

            GUIAction(

                name="open_properties"

            )

        )

        for addon in construction.addons:

            actions.append(

                GUIAction(

                    name=addon.name

                )

            )

        return GUIPlan(

            actions=actions

        )