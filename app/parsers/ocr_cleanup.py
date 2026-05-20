import re
import unicodedata


OCR_REPLACEMENTS = {

    "O": "0",

    "o": "0",

    "|": "1",

    "I": "1",

    "l": "1",

    ",": ".",

    "*": "x",

    "×": "x",

    "-": "x",
}


def remove_polish_chars(
    text: str
):

    normalized = unicodedata.normalize(
        "NFKD",
        text
    )

    return "".join(

        c

        for c in normalized

        if not unicodedata.combining(c)
    )


def cleanup_ocr_text(
    text: str
):

    text = remove_polish_chars(
        text
    )

    tokens = text.split()

    cleaned = []


    for token in tokens:

        if any(
            c.isdigit()

            for c in token
        ):

            for old, new in OCR_REPLACEMENTS.items():

                token = token.replace(
                    old,
                    new
                )

        cleaned.append(token)


    text = " ".join(
        cleaned
    )

    text = re.sub(

        r"\s+",

        " ",

        text
    )

    return text.strip()