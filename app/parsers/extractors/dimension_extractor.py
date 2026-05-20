from app.parsers.ocr_cleanup import (
    cleanup_ocr_text
)

import re


DIMENSION_PATTERNS = [

    r"(\d{3,4})\s*x\s*(\d{3,4})",

    r"(\d{3,4})\s*/\s*(\d{3,4})",

    r"(\d{3,4})\s*mm\s*x\s*(\d{3,4})",

    r"szer(?:okość|okosc)?[: ]+(\d{3,4}).*?wys(?:okość|okosc)?[: ]+(\d{3,4})",
]


def extract_dimensions(
    text: str
):

    text = cleanup_ocr_text(
        text
    )

    text = text.lower()

    for pattern in DIMENSION_PATTERNS:

        match = re.search(
            pattern,
            text,
            re.DOTALL
        )

        if match:

            width = int(
                match.group(1)
            )

            height = int(
                match.group(2)
            )

            return {

                "width_mm": width,

                "height_mm": height,

                "confidence": 0.95
            }

    return None