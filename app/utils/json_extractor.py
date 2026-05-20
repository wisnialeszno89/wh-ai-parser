import json
import re


def extract_json(text: str):

    match = re.search(
        r"\{.*\}",
        text,
        re.DOTALL
    )

    if not match:

        raise ValueError(
            "Brak JSON w odpowiedzi AI"
        )

    return json.loads(
        match.group(0)
    )