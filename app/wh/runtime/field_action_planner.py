from app.wh.runtime.actions.action_registry import (
    ActionRegistry
)

from app.wh.runtime.openings.opening_types import (
    TILT_TURN,
    FIX
)


class FieldActionPlanner:

    def __init__(

        self

    ):

        self.registry = (

            ActionRegistry()

        )

    def plan(

        self,

        fields

    ):

        for field in fields:

            if field.opening == TILT_TURN:

                field.actions = [

                    self.registry.get(

                        "frame"

                    ),

                    self.registry.get(

                        "sash"

                    ),

                    self.registry.get(

                        "glass"

                    )

                ]

            elif field.opening == FIX:

                field.actions = [

                    self.registry.get(

                        "frame"

                    ),

                    self.registry.get(

                        "glass"

                    )

                ]

        return fields