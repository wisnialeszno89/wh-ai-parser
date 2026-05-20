VALID_TYPES = [
    "FIX",
    "RU",
    "R",
    "U",
    "HST",
    "PSK"
]


VALID_SHAPES = [
    "rectangle",
    "triangle",
    "trapezoid",
    "arch",
    "circle"
]

VALID_CONSTRUCTION_TYPES = [
    "window",
    "door",
    "hst",
    "facade"
]

VALID_CONSTRUCTION_CATEGORIES = [

    "single_window",

    "double_window",

    "triple_window",

    "balcony_door",

    "terrace_hst",

    "terrace_psk",

    "front_door",

    "corner_window",

    "facade",

    "arch_window",

    "trapezoid_window",

    "triangle_window",

    "round_window"
]
def detect_construction_category(
    construction
):

    shape = construction.get(
        "shape",
        "rectangle"
    )

    schema = construction.get(
        "schema",
        ""
    )

    width = construction.get(
        "dimensions",
        {}
    ).get(
        "width_mm",
        0
    )

    if shape == "arch":

        return "arch_window"

    if shape == "triangle":

        return "triangle_window"

    if shape == "trapezoid":

        return "trapezoid_window"

    if shape == "circle":

        return "round_window"

    if "HST" in schema:

        return "terrace_hst"

    if "PSK" in schema:

        return "terrace_psk"

    if width > 2400:

        return "facade"

    segment_count = count_segments(
        construction
    )

    if segment_count == 1:

        return "single_window"

    if segment_count == 2:

        return "double_window"

    if segment_count >= 3:

        return "triple_window"

    return "single_window"

def validate_construction_type(construction):

    t = construction.get(
        "construction_type",
        "window"
    )

    if t not in VALID_CONSTRUCTION_TYPES:

        return "window"

    return t


def generate_schema(construction):

    segments = construction.get("segments", [])

    types = []

    for s in segments:

        segment_type = s.get("type", "UNKNOWN")

        types.append(segment_type)

    return "|".join(types)


def count_segments(construction):

    return len(
        construction.get("segments", [])
    )


def detect_main_shape(construction):

    shape = construction.get(
        "shape",
        "rectangle"
    )

    if shape not in VALID_SHAPES:

        return "rectangle"

    return shape


def has_movable_mullion(construction):

    segments = construction.get("segments", [])

    for s in segments:

        if s.get("mullion") is True:

            return True

    return False


def total_segment_width(construction):

    total = 0

    for s in construction.get("segments", []):

        total += s.get(
            "width_mm",
            0
        )

    return total


def validate_segment_types(construction):

    errors = []

    for s in construction.get("segments", []):

        t = s.get("type")

        if t not in VALID_TYPES:

            errors.append(
                f"Nieznany typ segmentu: {t}"
            )

    return errors


def enrich_construction(construction):

    construction["category"] = (
    detect_construction_category(
        construction
    )
)

    construction["construction_type"] = (
    validate_construction_type(
        construction
    )
)

    construction["schema"] = generate_schema(
        construction
    )

    construction["segment_count"] = count_segments(
        construction
    )

    construction["shape"] = detect_main_shape(
        construction
    )

    construction["movable_mullion"] = has_movable_mullion(
        construction
    )

    construction["calculated_width_mm"] = total_segment_width(
        construction
    )

    return construction