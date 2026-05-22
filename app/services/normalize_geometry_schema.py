def normalize_geometry_schema(
    data
):

    result = {}

    result["category"] = (
        data.get(
            "category",
            "WINDOW"
        )
    )

    result["confidence"] = (
        float(
            data.get(
                "confidence",
                0.0
            )
        )
    )

    segments = []

    for s in data.get(
        "segments",
        []
    ):

        kind = (
            s.get(
                "kind",
                "FIX"
            )
            .upper()
            .strip()
        )

        if kind not in [
            "FIX",
            "R",
            "RU"
        ]:
            kind = "FIX"

        segments.append({

            "kind": kind
        })

    result["segments"] = (
        segments
    )

    return result