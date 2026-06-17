import json
from pathlib import Path


PATTERN_DIR = Path(
    "catalog/patterns"
)


def load_pattern(
    signature
):

    filename = (

        signature
        .lower()
        .replace(
            "|",
            "_"
        )

        + ".json"
    )

    path = (
        PATTERN_DIR
        / filename
    )

    print(
        "Loading:",
        path
    )

    if not path.exists():

        return None

    text = path.read_text(
        encoding="utf-8"
    ).strip()

    if not text:

        return None

    return json.loads(
        text
    )