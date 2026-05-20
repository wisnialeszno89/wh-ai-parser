import json

from pathlib import Path


INDEX_PATH = Path(
    "app/catalog/template_index.json"
)


def load_index():

    with open(
        INDEX_PATH,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


def calculate_distance(
    schema,
    item
):

    width_diff = abs(

        schema.width_mm
        -
        item["width"]
    )

    height_diff = abs(

        schema.height_mm
        -
        item["height"]
    )


    return (

        width_diff
        +
        height_diff
    )


def recommend_template(
    schema,
    construction_id
):

    index = load_index()

    candidates = []


    for item in index:

        if (

            item["construction_id"]
            !=
            construction_id
        ):

            continue


        distance = calculate_distance(

            schema,
            item
        )


        candidates.append({

            "distance":
                distance,

            "item":
                item
        })


    if not candidates:

        return None


    candidates.sort(

        key=lambda x:
        x["distance"]
    )


    return candidates[0]