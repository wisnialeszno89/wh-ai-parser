from app.knowledge.text.customer_language import (
    normalize_token
)


OPENING_MAP = {

    "FIX":
        "fixed",

    "RU":
        "tilt_turn",

    "R":
        "turn",

    "U":
        "tilt"
}


def build_segments(
    text
):

    segments = []

    for token in text.split():

        token = normalize_token(
            token
        )

        if token in OPENING_MAP:

            segments.append(

                {

                    "opening":

                        OPENING_MAP[
                            token
                        ]

                }

            )

    return segments