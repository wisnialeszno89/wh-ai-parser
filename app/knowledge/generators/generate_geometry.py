def generate_geometry(
    segment_count
):

    operations = []

    #
    # vertical mullions
    #

    for _ in range(
        segment_count - 1
    ):

        operations.append(
            {
                "operation":
                    "insert_vertical"
            }
        )

    #
    # fields
    #

    for index in range(
        segment_count
    ):

        operations.append(
            {
                "operation":
                    "create_segment",

                "segment":
                    index
            }
        )

    return operations