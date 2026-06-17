from app.wh.runtime.field_executor import (
    FieldExecutor
)


def test_field_executor():

    executor = FieldExecutor()

    fields = [

        {

            "id":1,

            "actions":[

                "frame",

                "sash",

                "glass"

            ]

        },

        {

            "id":2,

            "actions":[

                "frame",

                "glass"

            ]

        }

    ]

    result = executor.execute(

        fields

    )

    assert result is True