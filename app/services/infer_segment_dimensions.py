def infer_segment_dimensions(data: dict):

    total_width = data.get(
        "width_mm"
    )

    segments = data.get(
        "segments",
        []
    )

    if not total_width:
        return data

    if not segments:
        return data

    # =====================================
    # CHECK EXISTING WIDTHS
    # =====================================

    existing = True

    for s in segments:

        if not s.get("width_mm"):

            existing = False
            break

    if existing:
        return data

    # =====================================
    # AUTO DISTRIBUTE
    # =====================================

    segment_count = len(segments)

    per_segment = int(
        total_width / segment_count
    )

    for s in segments:

        s["width_mm"] = per_segment

    return data