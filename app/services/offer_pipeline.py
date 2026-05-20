from app.parsers.semantic_offer_parser import (
    parse_multiple_constructions
)

from app.services.construction_matcher import (
    match_construction
)


def build_offer_pipeline(
    text: str
):

    constructions = parse_multiple_constructions(
        text
    )

    results = []


    for schema in constructions:

        match = match_construction(
            schema
        )

        results.append({

            "schema": schema,

            "match": match,
        })


    return results