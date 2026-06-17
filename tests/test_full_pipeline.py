from app.knowledge.text.text_to_schema import (
    text_to_schema
)

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


def test_customer_text():

    schema = text_to_schema(

        "1500x1400 FIX RU FIX"

    )

    operations = schema_to_operations(

        {
            "segments":
                schema.segments
        }

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