from app.ui.agent.operation_schema import (
    Operation
)

from app.ui.agent.pattern_registry import (
    get_pattern_definition
)


def build_operations_from_pattern(
    pattern_name: str
):

    definition = (

        get_pattern_definition(
            pattern_name
        )
    )

    if not definition:

        return []

    operations = []

    for op_name in (

        definition[
            "operations"
        ]
    ):

        operations.append(

            Operation(

                operation=op_name,

                params={}
            )
        )

    return operations