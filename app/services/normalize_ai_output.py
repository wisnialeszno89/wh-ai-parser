from app.services.construction_matcher import (
    match_construction
)


def normalize_ai_output(ai_data: dict):

    # =====================================
    # FALLBACKS
    # =====================================

    if (
        "construction_description"
        not in ai_data
    ):

        if "typ_konstrukcji" in ai_data:

            ai_data[
                "construction_description"
            ] = ai_data[
                "typ_konstrukcji"
            ]

    # =====================================
    # MATCH CONSTRUCTION
    # =====================================

    description = ai_data.get(
        "construction_description",
        ""
    )

    match = match_construction(
        description
    )

    construction = match.get(
        "construction"
    )

    if construction:

        ai_data[
            "matched_construction"
        ] = construction["id"]

    else:

        ai_data[
            "matched_construction"
        ] = None

    ai_data["match_score"] = round(
        match["score"],
        2
    )

    return ai_data