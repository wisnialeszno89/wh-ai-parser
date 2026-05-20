from config import DEFAULTS

from construction_defaults import (
    SEGMENT_TYPE_MAP,
    MATERIAL_MAP,
    SHAPE_MAP
)

from schema_engine import enrich_construction


def build_schema(construction):

    segments = construction.get("segments", [])

    types = []

    for s in segments:

        types.append(
            s.get("type", "UNK")
        )

    return "|".join(types)


def calculate_total_width(construction):

    segments = construction.get("segments", [])

    total = 0

    for s in segments:

        total += s.get("width_mm", 0)

    return total


def normalize_shape(window):

    raw_shape = str(
        window.get(
            "shape",
            "rectangle"
        )
    ).lower()

    for key, value in SHAPE_MAP.items():

        if key in raw_shape:

            window["shape"] = value

            return window

    window["shape"] = "rectangle"

    return window


def normalize_segment_types(window):

    segments = window.get("segments", [])

    for s in segments:

        raw_type = str(
            s.get("type", "")
        ).lower()

        normalized = "UNKNOWN"

        for key, value in SEGMENT_TYPE_MAP.items():

            if key in raw_type:

                normalized = value

                break

        s["type"] = normalized

    return window


def normalize_material(window):

    raw_material = str(
        window.get(
            "material",
            ""
        )
    ).lower()

    normalized = "UNKNOWN"

    for key, value in MATERIAL_MAP.items():

        if key in raw_material:

            normalized = value

            break

    window["material"] = normalized

    return window


def normalize_window(window):

    # ============================================
    # SHAPE
    # ============================================

    window = normalize_shape(window)

    # ============================================
    # SEGMENT TYPES
    # ============================================

    window = normalize_segment_types(window)

    # ============================================
    # MATERIAL
    # ============================================

    window = normalize_material(window)

    # ============================================
    # SCHEMA
    # ============================================

    window["schema"] = build_schema(window)

    # ============================================
    # TOTAL WIDTH
    # ============================================

    window["total_width_mm"] = calculate_total_width(window)

    # ============================================
    # DEFAULTS
    # ============================================

    material = window.get("material")

    defaults = DEFAULTS.get(material)

    if defaults:

        for key, value in defaults.items():

            if not window.get(key):

                window[key] = value

    # ============================================
    # ENRICH ENGINE
    # ============================================

    window = enrich_construction(window)

    return window