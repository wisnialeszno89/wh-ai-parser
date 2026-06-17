from app.wh.runtime.gui_action import (
    GUIAction
)

from app.wh.runtime.opening_strategy import (
    OpeningStrategy
)


class HSTStrategy(

    OpeningStrategy

):

    def plan(

        self

    ):

        return [

            GUIAction(

                name="sash"

            ),

            GUIAction(

                name="hardware"

            ),

            GUIAction(

                name="add_glass"

            )

        ]