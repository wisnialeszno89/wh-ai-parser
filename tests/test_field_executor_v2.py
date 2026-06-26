from app.wh.runtime.field_executor_v2 import (
    FieldExecutorV2
)

from app.wh.runtime.action import (
    Action
)

from app.wh.vision.field_region import (
    FieldRegion
)

from app.wh.model.opening import (
    Opening
)


def test_field_executor_v2():

    executor = FieldExecutorV2()

    region = FieldRegion(

        left=100,

        top=200,

        right=800,

        bottom=700,

        id=1,

        opening=Opening.TILT_TURN

    )

    region.actions = [

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

    result = executor.execute(

        [

            region

        ]

    )

    assert result is True