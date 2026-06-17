from unittest.mock import (
    MagicMock
)

from app.wh.runtime.field_executor import (
    FieldExecutor
)

from app.wh.runtime.fields.field import (
    Field
)


def test_field_executor():

    executor = FieldExecutor()

    executor.executor = MagicMock()

    fields = [

        Field(

            id=1,

            x=550,

            y=700,

            actions=[

                "frame",

                "sash",

                "glass"

            ]

        ),

        Field(

            id=2,

            x=1150,

            y=700,

            actions=[

                "frame",

                "glass"

            ]

        )

    ]

    executor.execute(

        fields

    )

    assert (

        executor.executor.execute_action.call_count

        == 5

    )