from app.models.enums import (
    ConstructionCategory,
    OpeningType,
    SegmentKind
)


def validate_schema(schema):

    errors = []

    if schema.width_mm <= 0:

        errors.append(
            "Invalid width"
        )

    if schema.height_mm <= 0:

        errors.append(
            "Invalid height"
        )

    if not schema.segments:

        errors.append(
            "Construction has no segments"
        )

    for segment in schema.segments:

        if (
            segment.kind == SegmentKind.FIX
            and segment.has_handle
        ):

            errors.append(
                "FIX segment cannot have handle"
            )

        if (
            segment.kind == SegmentKind.FIX
            and segment.opening != OpeningType.FIXED
        ):

            errors.append(
                "FIX segment must use FIXED opening"
            )

        if (
            schema.category == ConstructionCategory.HST
            and segment.opening != OpeningType.HST
        ):

            errors.append(
                "HST construction requires HST openings"
            )

        if (
            schema.category == ConstructionCategory.PSK
            and segment.opening != OpeningType.PSK
        ):

            errors.append(
                "PSK construction requires PSK openings"
            )

    return errors