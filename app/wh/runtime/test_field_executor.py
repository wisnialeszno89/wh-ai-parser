from unittest.mock import (
    MagicMock
)

from app.wh.runtime.field_executor import (
    FieldExecutor
)

from app.wh.runtime.fields.field import (
    Field
)

from app.wh.runtime.actions.action import (
    Action
)


def test_field_executor():

    executor = FieldExecutor()

    executor.executor = (

        MagicMock()

    )

    fields = [

        Field(

            id=1,

            x=500,

            y=700,

            actions=[

                Action(

                    "frame",

                    "frame_button.png"

                ),

                Action(

                    "glass",

                    "glass_button.png"

                )

            ]

        )

    ]

    result = executor.execute(

        fields

    )

    assert (

        executor.executor.execute_action.call_count

        == 2

    )

    assert result is True