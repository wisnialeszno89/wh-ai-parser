def assign_roles(
    segments
):

    result = []

    for segment in segments:

        role = segment.get(
            "kind"
        )

        result.append({

            **segment,

            "role": role
        })

    return result