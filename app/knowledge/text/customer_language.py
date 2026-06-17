from app.knowledge.text.polish_abbreviations import (
    POLISH_ABBREVIATIONS
)

from app.knowledge.text.german_abbreviations import (
    GERMAN_ABBREVIATIONS
)


ABBREVIATIONS = {

    **POLISH_ABBREVIATIONS,

    **GERMAN_ABBREVIATIONS
}


def normalize_token(
    token
):

    token = token.upper()

    return ABBREVIATIONS.get(

        token,

        token
    )