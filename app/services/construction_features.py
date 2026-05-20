from app.models.enums import (
    OpeningType,
    SegmentKind
)


def extract_construction_features(schema):

    openings = set()

    has_fix = False

    active_count = 0

    opening_count = 0

    segment_kinds = []

    for segment in schema.segments:

        segment_kinds.append(
            segment.kind.value
        )

        if segment.opening:

            openings.add(
                segment.opening.value
            )

        if (
            segment.kind == SegmentKind.FIX
        ):

            has_fix = True

        if (
            segment.opening
            and segment.opening != OpeningType.FIXED
        ):

            opening_count += 1

        if segment.is_active:

            active_count += 1

    has_movable_mullion = (

        opening_count >= 2
        and not has_fix
    )

    is_symmetrical = False

    if len(schema.segments) == 2:

        left = schema.segments[0]
        right = schema.segments[1]

        if (
            left.opening
            ==
            right.opening
        ):

            is_symmetrical = True

    return {

        "category": schema.category.value,

        "segment_count": len(
            schema.segments
        ),

        "openings": sorted(
            list(openings)
        ),

        "segment_kinds": sorted(
            segment_kinds
        ),

        "has_fix": has_fix,

        "opening_count": opening_count,

        "active_count": active_count,

        "has_movable_mullion": (
            has_movable_mullion
        ),

        "symmetrical": is_symmetrical,

        "width_mm": schema.width_mm,

        "height_mm": schema.height_mm
    }