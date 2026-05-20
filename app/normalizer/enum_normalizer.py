from app.models.enums import (
    ConstructionCategory,
    OpeningType,
    SegmentKind
)


OPENING_MAPPING = {

    "fix": OpeningType.FIXED,
    "fixed": OpeningType.FIXED,

    "r": OpeningType.TURN,
    "turn": OpeningType.TURN,

    "u": OpeningType.TILT,
    "tilt": OpeningType.TILT,

    "ru": OpeningType.TILT_TURN,
    "tilt_turn": OpeningType.TILT_TURN,
    "tilt-turn": OpeningType.TILT_TURN,
    "tilt turn": OpeningType.TILT_TURN,
    "uchylno-rozwierne": OpeningType.TILT_TURN,

    "slide": OpeningType.SLIDING,
    "sliding": OpeningType.SLIDING,

    "hst": OpeningType.HST,

    "psk": OpeningType.PSK,
}


SEGMENT_KIND_MAPPING = {

    "fix": SegmentKind.FIX,

    "fixed": SegmentKind.FIX,

    "left": SegmentKind.LEFT,

    "right": SegmentKind.RIGHT,

    "middle": SegmentKind.MIDDLE,

    "full": SegmentKind.FULL,
}


CATEGORY_MAPPING = {

    "window": ConstructionCategory.WINDOW,

    "door": ConstructionCategory.DOOR,

    "hst": ConstructionCategory.HST,

    "psk": ConstructionCategory.PSK,

    "garage_gate":
        ConstructionCategory.GARAGE_GATE,

    "roller_shutter":
        ConstructionCategory.ROLLER_SHUTTER,
}


def normalize_opening(
    value: str | None
):

    if value is None:

        return None

    return OPENING_MAPPING.get(

        value.lower().strip()
    )


def normalize_segment_kind(
    value: str
):

    return SEGMENT_KIND_MAPPING.get(

        value.lower().strip()
    )


def normalize_category(
    value: str
):

    return CATEGORY_MAPPING.get(

        value.lower().strip()
    )