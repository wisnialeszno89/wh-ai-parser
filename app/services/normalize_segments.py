SEGMENT_TYPE_MAP = {

    # =====================================
    # FIX
    # =====================================

    "fix": {
        "kind": "fixed",
        "opening_mode": "FIX"
    },

    "fixed": {
        "kind": "fixed",
        "opening_mode": "FIX"
    },

    # =====================================
    # RU
    # =====================================

    "ru": {
        "kind": "sash",
        "opening_mode": "RU"
    },

    "r": {
        "kind": "sash",
        "opening_mode": "R"
    },

    # =====================================
    # HST
    # =====================================

    "hst": {
        "kind": "sliding",
        "opening_mode": "HST"
    },

    "movable": {
        "kind": "sliding",
        "opening_mode": "HST"
    },

    # =====================================
    # DOORS
    # =====================================

    "door": {
        "kind": "door",
        "opening_mode": "RU"
    },

    "balcony_door": {
        "kind": "door",
        "opening_mode": "RU"
    }
}


def normalize_segments(segments: list):

    normalized = []

    for i, segment in enumerate(segments):

        # =====================================
        # RAW TYPE
        # =====================================

        raw_type = (

            segment.get("type")

            or

            segment.get("segment_type")

            or

            ""

        ).lower()

        mapped = SEGMENT_TYPE_MAP.get(
            raw_type
        )

        if not mapped:

            continue

        normalized.append({

            "segment_id": i + 1,

            "kind": mapped["kind"],

            "opening_mode": mapped[
                "opening_mode"
            ],

            "width_mm": segment.get(
                "width_mm",
                0
            ),

            "height_mm": segment.get(
                "height_mm"
            ),

            "opening_side": (

                segment.get(
                    "opening_side"
                )

                or

                segment.get(
                    "opening_direction"
                )
            )
        })

    return normalized