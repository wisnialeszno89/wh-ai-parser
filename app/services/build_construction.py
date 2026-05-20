from app.catalog.load_constructions import (
    load_constructions
)

from app.services.normalize_segments import (
    normalize_segments
)


def build_construction(ai_data: dict):

    matched = ai_data.get(
        "matched_construction"
    )

    constructions = load_constructions()

    template = None

    for item in constructions:

        if item["id"] == matched:

            template = item
            break

    # =====================================
    # FALLBACK
    # =====================================

    if not template:

        return ai_data

    # =====================================
    # SEGMENTS
    # =====================================

    segments = ai_data.get(
        "segments"
    )

    if ai_data.get("segments"):

    segments = normalize_segments(
        ai_data["segments"]
    )

    else:

    segments = template.get(
        "segments",
        []
    )

    # =====================================
    # BUILD RESULT
    # =====================================

    result = {

        "construction_description": matched,

        "construction_id": ai_data.get(
            "construction_id",
            1
        ),

        "matched_construction": matched,

        "category": template.get(
            "category",
            "window"
        ),

        "width_mm": ai_data.get(
            "width_mm"
        ),

        "height_mm": ai_data.get(
            "height_mm"
        ),

        "color_inside": ai_data.get(
            "color_inside",
            "white"
        ),

        "color_outside": ai_data.get(
            "color_outside",
            "white"
        ),

        "glass_type": ai_data.get(
            "glass_type",
            "triple"
        ),

        "profile_system": ai_data.get(
            "profile_system",
            "unknown"
        ),

        "segments": segments,
    }

    # =====================================
    # OPTIONALS
    # =====================================

    if "roller_shutter" in template:

        result["roller_shutter"] = (
            template["roller_shutter"]
        )

    if "mosquito_net" in template:

        result["mosquito_net"] = (
            template["mosquito_net"]
        )

    # =====================================
    # DEBUG
    # =====================================

    print("\n========== TEMPLATE ==========\n")
    print(template)

    print("\n========== TEMPLATE SEGMENTS ==========\n")
    print(template.get("segments"))

    print("\n========== FINAL SEGMENTS ==========\n")
    print(segments)

    print("\n========== FINAL RESULT ==========\n")
    print(result)

    return result