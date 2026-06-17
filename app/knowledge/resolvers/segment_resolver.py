from app.knowledge.types.opening_types import (
    OpeningType
)


OPENING_TO_OPERATION = {

    OpeningType.FIX.value:
        "create_fix",

    OpeningType.RU.value:
        "create_ru",

    OpeningType.R.value:
        "create_r",

    OpeningType.U.value:
        "create_u",

    OpeningType.DOOR.value:
        "create_door",

    OpeningType.HST_LEFT.value:
        "create_hst_left",

    OpeningType.HST_RIGHT.value:
        "create_hst_right",

    OpeningType.PSK_LEFT.value:
        "create_psk_left",

    OpeningType.PSK_RIGHT.value:
        "create_psk_right"
}


def resolve_segment(
    segment
):

    opening = segment.get(
        "opening"
    )

    return OPENING_TO_OPERATION.get(
        opening
    )