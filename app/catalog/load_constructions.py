import json

from pathlib import Path


CATALOG_PATH = Path(
    "app/catalog/constructions"
)


def load_constructions():

    constructions = []


    for file in CATALOG_PATH.rglob(
        "*.json"
    ):

        with open(
            file,
            "r",
            encoding="utf-8"
        ) as f:

            constructions.append(

                json.load(f)
            )


    return constructions