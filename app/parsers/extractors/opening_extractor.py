from app.schema.construction_schema import (
    Segment
)

from app.models.enums import (
    SegmentKind,
    OpeningType
)


OPENING_KEYWORDS = {

    "ru": OpeningType.TILT_TURN,

    "r": OpeningType.TURN,

    "u": OpeningType.TILT,

    "fix": OpeningType.FIXED,

    "hst": OpeningType.SLIDING,

    "slide": OpeningType.SLIDING,

    "sliding": OpeningType.SLIDING,

    "psk": OpeningType.SLIDING,
}


def extract_segments(
    text: str
):

    text = text.lower()

    normalized = text.replace(
        "/",
        " "
    ).replace(
        "|",
        " "
    )

    tokens = normalized.split()

    segments = []


    for token in tokens:

        token = token.strip()

        if token not in OPENING_KEYWORDS:

            continue


        opening = OPENING_KEYWORDS[
            token
        ]


        if opening == OpeningType.FIXED:

            kind = SegmentKind.FIX


        elif opening == OpeningType.SLIDING:

            if not segments:

                kind = SegmentKind.LEFT

            else:

                kind = SegmentKind.RIGHT


        else:

            active_segments = [

                s

                for s in segments

                if s.opening != OpeningType.FIXED
            ]


            if not active_segments:

                kind = SegmentKind.LEFT

            else:

                kind = SegmentKind.RIGHT


        segments.append(

            Segment(

                kind=kind,

                opening=opening,

                is_active=(

                    opening
                    !=
                    OpeningType.FIXED
                )
            )
        )


    if (

        len(segments) == 1

        and

        segments[0].opening
        == OpeningType.SLIDING
    ):

        segments.append(

            Segment(

                kind=SegmentKind.RIGHT,

                opening=OpeningType.FIXED,

                is_active=False
            )
        )


    return segments