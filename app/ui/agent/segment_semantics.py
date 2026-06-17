def enrich_segments(
    construction
):

    segments = construction.get(
        "segments",
        []
    )

    enriched = []

    count = len(
        segments
    )

    for index, segment in enumerate(
        segments
    ):

        opening = segment.get(
            "opening"
        )

        if opening == "fixed":

            kind = "fixed"

        else:

            kind = "sash"

        if count == 1:

            position = "single"

        elif index == 0:

            position = "left"

        elif index == count - 1:

            position = "right"

        else:

            position = "center"

        enriched.append({

            **segment,

            "kind": kind,

            "position": position
        })

    return enriched