from app.ui.agent.construction_patterns import (
    detect_pattern
)

from app.ui.agent.pattern_registry import (
    get_pattern_definition
)

from app.ui.agent.operation_schema import (
    Operation
)


def schema_to_operations(
    construction
):

    segments = construction.get(
        "segments",
        []
    )

    pattern = detect_pattern(
        segments
    )

    definition = (
        get_pattern_definition(
            pattern
        )
    )

    if not definition:

        return []

    operations = []

    operation_names = (
        definition["operations"]
    )

    for index, operation_name in enumerate(

        operation_names

    ):

        params = {}

        if (

            operation_name
            ==
            "create_sash"

            and

            len(segments) >= 1
        ):

            params["opening"] = (

                segments[0].get(
                    "opening"
                )
            )

        elif (

            operation_name
            ==
            "create_left_sash"

            and

            len(segments) >= 1
        ):

            params["opening"] = (

                segments[0].get(
                    "opening"
                )
            )

        elif (

            operation_name
            ==
            "create_right_sash"

            and

            len(segments) >= 2
        ):

            params["opening"] = (

                segments[1].get(
                    "opening"
                )
            )

        elif (

            operation_name
            ==
            "create_left_fix"
        ):

            params["opening"] = (
                "fixed"
            )

        elif (

            operation_name
            ==
            "create_right_fix"
        ):

            params["opening"] = (
                "fixed"
            )

        operations.append(

            Operation(

                operation=
                    operation_name,

                params=params
            )
        )

    return operations