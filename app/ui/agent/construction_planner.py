from app.ui.agent.operation_schema import (
    Operation
)


def build_operations(
    construction
):

    operations = []

    segments = construction.get(
        "segments",
        []
    )

    segment_count = len(
        segments
    )

    if segment_count == 1:

        operations.append(

            Operation(

                operation="create_single_field",

                params={}
            )
        )

    elif segment_count == 2:

        operations.append(

            Operation(

                operation="insert_vertical",

                params={}
            )
        )

        operations.append(

            Operation(

                operation="create_left_segment",

                params={
                    "opening":
                    segments[0].get(
                        "opening"
                    )
                }
            )
        )

        operations.append(

            Operation(

                operation="create_right_segment",

                params={
                    "opening":
                    segments[1].get(
                        "opening"
                    )
                }
            )
        )

    return operations