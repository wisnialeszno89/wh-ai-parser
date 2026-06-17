# app/knowledge/signatures/build_signature.py

from app.knowledge.types.opening_types import (
    OpeningType
)


OPENING_TO_SIGNATURE = {

    OpeningType.FIX.value:
        "FIX",

    OpeningType.RU.value:
        "RU",

    OpeningType.R.value:
        "R",

    OpeningType.U.value:
        "U",

    OpeningType.DOOR.value:
        "DOOR",

    OpeningType.HST_LEFT.value:
        "HSTL",

    OpeningType.HST_RIGHT.value:
        "HSTR",

    OpeningType.PSK_LEFT.value:
        "PSKL",

    OpeningType.PSK_RIGHT.value:
        "PSKR",
}


def build_signature(segments):

    tokens = []

    for segment in segments:

        opening = segment.get(
            "opening"
        )

        token = OPENING_TO_SIGNATURE.get(
            opening,
            "UNK"
        )

        tokens.append(
            token
        )

    return "|".join(
        tokens
    )