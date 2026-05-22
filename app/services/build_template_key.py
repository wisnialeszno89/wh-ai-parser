def build_template_key(
    construction
):

    segments = construction.get(
        "segments",
        []
    )

    kinds = []

    for s in segments:

        kinds.append(
            s.get(
                "kind",
                "FIX"
            )
        )

    return "_".join(kinds)