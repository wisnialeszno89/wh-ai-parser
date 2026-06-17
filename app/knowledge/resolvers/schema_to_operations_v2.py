from app.knowledge.signatures.build_signature import (
    build_signature
)

from app.knowledge.catalog.load_patterns import (
    load_pattern
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

    signature = build_signature(
        segments
    )
    print(
    "SIGNATURE =",
    signature
    )
    pattern = load_pattern(
        signature
    )
    print(
    "PATTERN =",
    pattern
    )
    if not pattern:

        return []

    operations = []

    for op in pattern[
        "operations"
    ]:

        operation_name = op[
            "operation"
        ]

        #
        # geometry operation
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
        # semantic operation
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