from app.knowledge.resolvers.schema_to_operations_v4 import (
    schema_to_operations
)


def operation_names(
    operations
):

    return [

        op.operation

        for op

        in operations
    ]


def test_fix_ru_fix():

    construction = {

        "segments": [

            {
                "opening":
                    "fixed"
            },

            {
                "opening":
                    "tilt_turn"
            },

            {
                "opening":
                    "fixed"
            }

        ]

    }

    operations = schema_to_operations(
        construction
    )

    assert operation_names(
        operations
    ) == [

        "insert_vertical",

        "insert_vertical",

        "create_fix",

        "create_ru",

        "create_fix"

    ]