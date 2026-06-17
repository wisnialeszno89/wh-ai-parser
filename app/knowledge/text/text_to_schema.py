from app.knowledge.construction.construction_schema import (
    ConstructionSchema
)

from app.knowledge.text.normalize_separators import (
    normalize_separators
)

from app.knowledge.text.expand_counts import (
    expand_counts
)

from app.knowledge.text.extract_dimensions import (
    extract_dimensions
)

from app.knowledge.text.build_segments import (
    build_segments
)


def text_to_schema(
    text
):

    text = text.upper()

    text = normalize_separators(
        text
    )

    text = expand_counts(
        text
    )

    width, height = extract_dimensions(
        text
    )

    segments = build_segments(
        text
    )

    return ConstructionSchema(

        width_mm=
            width,

        height_mm=
            height,

        segments=
            segments

    )