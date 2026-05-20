from app.vision.preprocessing.split_segments import (
    split_segments
)

from app.vision.preprocessing.enhance_technical_drawing import (
    enhance_technical_drawing
)

from app.vision.services.classify_segment_service import (
    classify_segment
)

from app.vision.preprocessing.detect_diagonals import (
    detect_diagonals
)


def build_construction(
    image_path: str
):

    segments = split_segments(
        image_path
    )

    results = []

    for i, segment_path in enumerate(segments):

        enhanced_path = (
            f"app/vision/debug/"
            f"enhanced_{i}.jpg"
        )

        enhance_technical_drawing(
            segment_path,
            enhanced_path
        )

        diagonals = detect_diagonals(
            enhanced_path
        )

        if len(diagonals) == 0:

            opening = "FIX"

        else:

            raw = classify_segment(
                enhanced_path
            )

            if "RU" in raw:

                opening = "RU"

            else:

                opening = "R"

        results.append(
            opening
        )

    return results