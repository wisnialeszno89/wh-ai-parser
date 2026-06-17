from app.knowledge.semantics.segment_semantic import (
    SegmentSemantic
)

from app.knowledge.types.opening_types import (
    OpeningType
)


def resolve_segment(
    segment
):

    opening = segment.get(
        "opening"
    )

    if opening == OpeningType.FIX.value:

        return SegmentSemantic(

            opening=opening,

            operation="create_fix",

            role="fix"
        )

    if opening == OpeningType.RU.value:

        return SegmentSemantic(

            opening=opening,

            operation="create_ru",

            role="sash"
        )

    if opening == OpeningType.R.value:

        return SegmentSemantic(

            opening=opening,

            operation="create_r",

            role="sash"
        )

    if opening == OpeningType.U.value:

        return SegmentSemantic(

            opening=opening,

            operation="create_u",

            role="sash"
        )

    return None