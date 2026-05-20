def validate_construction(c):

    errors = []

    # ============================================
    # HEIGHT
    # ============================================

    height = c.get("height_mm", 0)

    if height < 300 or height > 4000:

        errors.append(
            f"Nieprawidłowa wysokość: {height}"
        )

    # ============================================
    # TOTAL WIDTH
    # ============================================

    total_width = c.get("total_width_mm", 0)

    if total_width < 300 or total_width > 12000:

        errors.append(
            f"Podejrzana szerokość całkowita: {total_width}"
        )

    # ============================================
    # SEGMENTS
    # ============================================

    segments = c.get("segments", [])

    if len(segments) == 0:

        errors.append(
            "Brak segmentów"
        )

    # ============================================
    # SEGMENT VALIDATION
    # ============================================

    valid_types = [
        "FIX",
        "RU",
        "R",
        "U",
        "HST",
        "PSK",
        "UNKNOWN"
    ]

    for s in segments:

        width = s.get("width_mm", 0)

        if width < 200 or width > 3000:

            errors.append(
                f"Podejrzana szerokość segmentu: {width}"
            )

        if s.get("type") not in valid_types:

            errors.append(
                f"Nieznany typ: {s.get('type')}"
            )

    return errors