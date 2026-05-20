import json
import re

from pathlib import Path


INDEX_PATH = Path(
    "app/catalog/template_index.json"
)


def extract_dimensions_from_filename(
    path: str
):

    match = re.search(

        r"(\d{3,4})x(\d{3,4})",

        path.lower()
    )

    if not match:

        return None


    return (

        int(match.group(1)),

        int(match.group(2))
    )


def add_template(

    construction_id: str,

    template_path: str
):

    dimensions = extract_dimensions_from_filename(
        template_path
    )

    if not dimensions:

        raise ValueError(
            "Cannot detect dimensions from filename"
        )


    width, height = dimensions


    if INDEX_PATH.exists():

        with open(
            INDEX_PATH,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

    else:

        data = []


    entry = {

        "construction_id":
            construction_id,

        "width":
            width,

        "height":
            height,

        "template":
            template_path
    }


    data.append(entry)


    with open(
        INDEX_PATH,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(

            data,
            f,
            indent=2
        )


    return entry