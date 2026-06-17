from app.knowledge.generators.generate_geometry import (
    generate_geometry
)

from app.knowledge.operations.operation_schema import (
    Operation
)

from app.knowledge.resolvers.segment_resolver import (
    resolve_segment
)


def schema_to_operations(
    construction
):

    segments = construction.get(
        "segments",
        []
    )

    geometry = generate_geometry(
        len(
            segments
        )
    )

    operations = []

    for op in geometry:

        operation_name = op[
            "operation"
        ]

        #
        # geometry operations
        #

        if (

            operation_name
            !=
            "create_segment"

        ):

            operations.append(

                Operation(

                    operation=
                        operation_name,

                    params={}
                )
            )

            continue

        #
        # semantic operations
        #

        segment_index = op[
            "segment"
        ]

        segment = segments[
            segment_index
        ]

        semantic_operation = (

            resolve_segment(
                segment
            )
        )

        operations.append(

            Operation(

                operation=
                    semantic_operation,

                params={}
            )
        )

    return operations