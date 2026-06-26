from app.wh.runtime.action import (
    Action
)

from app.wh.model.opening import (
    Opening
)


class SegmentActionPlanner:

    def plan(

        self,

        opening

    ):

        if opening in (

            Opening.TILT_TURN,

            Opening.TURN,

            Opening.TILT

        ):

            return [

                Action(

                    name="frame",

                    template_path=

                    "tests/data/frame_button.png"

                ),

                Action(

                    name="sash",

                    template_path=

                    "tests/data/sash_button.png"

                ),

                Action(

                    name="glass",

                    template_path=

                    "tests/data/glass_button.png"

                )

            ]

        if opening == (

            Opening.FIX

        ):

            return [

                Action(

                    name="frame",

                    template_path=

                    "tests/data/frame_button.png"

                ),

                Action(

                    name="glass",

                    template_path=

                    "tests/data/glass_button.png"

                )

            ]

        if opening == (

            Opening.PSK

        ):

            return [

                Action(

                    name="frame",

                    template_path=

                    "tests/data/frame_button.png"

                ),

                Action(

                    name="psk_sash",

                    template_path=

                    "tests/data/psk_sash_button.png"

                ),

                Action(

                    name="glass",

                    template_path=

                    "tests/data/glass_button.png"

                )

            ]

        if opening == (

            Opening.HST

        ):

            return [

                Action(

                    name="frame",

                    template_path=

                    "tests/data/frame_button.png"

                ),

                Action(

                    name="hst_active_leaf",

                    template_path=

                    "tests/data/hst_active_leaf_button.png"

                ),

                Action(

                    name="hst_passive_leaf",

                    template_path=

                    "tests/data/hst_passive_leaf_button.png"

                ),

                Action(

                    name="glass",

                    template_path=

                    "tests/data/glass_button.png"

                )

            ]

        return []