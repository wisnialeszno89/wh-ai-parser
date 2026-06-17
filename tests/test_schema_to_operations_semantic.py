from app.knowledge.resolvers.schema_to_operations_v2 import (
    schema_to_operations
)


def test_fix_ru_fix_semantic():

    construction = {

        "segments": [

            {
                "opening": "fixed"
            },

            {
                "opening": "tilt_turn"
            },

            {
                "opening": "fixed"
            }

        ]
    }

    operations = schema_to_operations(
        construction
    )

    names = [

        op.operation

        for op

        in operations
    ]

    assert names == [

        "insert_vertical",

        "insert_vertical",

        "create_fix",

        "create_ru",

        "create_fix"

    ]