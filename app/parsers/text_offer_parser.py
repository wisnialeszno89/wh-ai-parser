import re

from app.schema.construction_schema import (
    ConstructionSchema,
    Segment
)

from app.normalizer.enum_normalizer import (
    normalize_category,
    normalize_opening,
    normalize_segment_kind
)


def parse_dimensions(text):

    match = re.search(
        r"(\d+)\s*x\s*(\d+)",
        text
    )

    if not match:

        return None, None

    return (
        int(match.group(1)),
        int(match.group(2))
    )


def detect_segments(text):

    segments = []

    if "DKL/DKR" in text:

        segments = [

            Segment(
                kind=normalize_segment_kind(
                    "left"
                ),

                opening=normalize_opening(
                    "tilt_turn"
                )
            ),

            Segment(
                kind=normalize_segment_kind(
                    "right"
                ),

                opening=normalize_opening(
                    "tilt_turn"
                )
            )
        ]

    elif "Festelement" in text:

        segments = [

            Segment(
                kind=normalize_segment_kind(
                    "fix"
                ),

                opening=normalize_opening(
                    "fixed"
                )
            )
        ]

    return segments


def detect_profile(text):

    profiles = [

        "VEKA Motion",
        "VEKA Softline 70",
        "VEKA Softline 82",
        "Aluplast",
        "Salamander",
        "Gealan"
    ]

    for profile in profiles:

        if profile.lower() in text.lower():

            return profile

    return ""


def detect_category(text):

    text = text.lower()

    if "hst" in text:

        return normalize_category(
            "hst"
        )

    if "psk" in text:

        return normalize_category(
            "psk"
        )

    if "drzwi" in text:

        return normalize_category(
            "door"
        )

    return normalize_category(
        "window"
    )


def parse_offer_text(text):

    width, height = (
        parse_dimensions(text)
    )

    profile = detect_profile(
        text
    )

    glass = None

    glass_match = re.search(
        r"Ug=([\d\.]+)",
        text
    )

    if glass_match:

        glass = (
            glass_match.group(1)
        )

    return ConstructionSchema(

        category=detect_category(
            text
        ),

        width_mm=width or 0,

        height_mm=height or 0,

        profile_system=profile or "",

        glass_type=glass or "",

        color_inside="",

        color_outside="",

        segments=detect_segments(
            text
        )
    )