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


def match_construction(
    schema
):

    constructions = load_constructions()

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