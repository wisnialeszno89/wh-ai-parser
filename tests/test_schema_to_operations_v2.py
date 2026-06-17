from app.knowledge.resolvers.schema_to_operations_v2 import (
    schema_to_operations
)


def test_fix_ru_fix():

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

    assert len(
        operations
    ) == 5