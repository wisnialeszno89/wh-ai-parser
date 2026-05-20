import json

from app.vision.models.segment_result import (
    SegmentResult
)


def parse_segment_response(
    raw: str
):

    data = json.loads(raw)

    segments = []

    for s in data.get(
        "segments",
        []
    ):

        segments.append(
            s["kind"]
        )

    return SegmentResult(
        segments=segments
    )