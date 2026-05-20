from app.schema.construction_schema import (
    ConstructionSchema
)

from app.models.enums import (
    ConstructionCategory
)

from app.parsers.extractors.dimension_extractor import (
    extract_dimensions
)

from app.parsers.extractors.category_extractor import (
    extract_category
)

from app.parsers.extractors.profile_extractor import (
    extract_profile
)

from app.parsers.extractors.glass_extractor import (
    extract_glass
)

from app.parsers.extractors.color_extractor import (
    extract_colors
)

from app.parsers.extractors.addons_extractor import (
    extract_addons
)
from app.parsers.block_splitter import (
    split_offer_blocks
)
from app.parsers.extractors.opening_extractor import (
    extract_segments
)


def parse_offer_text(
    text: str
):

    dimensions = extract_dimensions(
        text
    )

    category = extract_category(
        text
    )

    profile = extract_profile(
        text
    )

    glass = extract_glass(
        text
    )

    colors = extract_colors(
        text
    )

    addons = extract_addons(
        text
    )

    segments = extract_segments(
    text
    )
    return ConstructionSchema(

            category=(

            category["category"]

            if category

            else ConstructionCategory.WINDOW
        ),

        width_mm=(

            dimensions["width_mm"]

            if dimensions

            else 0
        ),

        height_mm=(

            dimensions["height_mm"]

            if dimensions

            else 0
        ),
        segments=segments,
        
        profile_system=(

            profile["profile_system"]

            if profile

            else ""
        ),

        glass_type=(

            glass["glass_type"]

            if glass

            else ""
        ),

        color_inside=(

            colors["color_inside"]

            if colors

            else ""
        ),

        color_outside=(

            colors["color_outside"]

            if colors

            else ""
        ),

        addons=(

            addons["addons"]

            if addons

            else []
        ),

        metadata={

            "glass": glass,

            "profile": profile,

            "colors": colors,

            "addons": addons,
        }
    )
    from app.parsers.block_splitter import (
    split_offer_blocks
)


def parse_multiple_constructions(
    text: str
):

    blocks = split_offer_blocks(
        text
    )

    results = []


    for block in blocks:

        schema = parse_offer_text(
            block
        )

        results.append(
            schema
        )


    return results