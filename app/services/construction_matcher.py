from app.catalog.load_constructions import (
    load_constructions
)


def calculate_score(
    schema,
    item
):

    score = 0

    features = item.get(
        "features",
        {}
    )


    if (

        schema.category.value

        ==

        features.get("category")
    ):

        score += 40


    if (

        len(schema.segments)

        ==

        features.get(
            "segment_count",
            0
        )
    ):

        score += 25


    openings = [

        s.opening.value

        for s in schema.segments

        if s.opening
    ]


    segment_kinds = [

        s.kind.value

        for s in schema.segments
    ]


    feature_openings = features.get(
        "openings",
        []
    )


    feature_segments = [

        s.get("kind")

        for s in item.get(
            "segments",
            []
        )
    ]


    for opening in openings:

        if opening in feature_openings:

            score += 10


    for kind in segment_kinds:

        if kind in feature_segments:

            score += 15


    if schema.width_mm > 2000:

        score += 5


    return score


def _match_text(
    description,
    constructions
):

    normalized = " ".join(
        str(description)
        .strip()
        .lower()
        .split()
    )

    if not normalized:

        return {

            "score": 0,

            "construction": None
        }

    for item in constructions:

        candidates = [

            item.get("id"),

            item.get("label"),

            item.get("category"),

            item.get("schema"),

            *item.get(
                "aliases",
                []
            )
        ]

        for candidate in candidates:

            if (

                candidate
                and
                " ".join(
                    str(candidate)
                    .strip()
                    .lower()
                    .split()
                )
                == normalized

            ):

                return {

                    "score": 100,

                    "construction":
                        item
                }

    return {

        "score": 0,

        "construction": None
    }


def match_construction(
    schema
):

    constructions = load_constructions()

    if isinstance(
        schema,
        str
    ):

        return _match_text(
            schema,
            constructions
        )

    best_match = None

    best_score = -1


    for item in constructions:

        score = calculate_score(
            schema,
            item
        )

        if score > best_score:

            best_score = score

            best_match = item


    return {

        "score": best_score,

        "construction":
            best_match
    }
