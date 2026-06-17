import os
import cv2

from app.ui.detection.detect_tool_candidates import (
    detect_tool_candidates
)


OUTPUT_DIR = "outputs/candidates"


def export_tool_candidates(

    image_path: str
):

    os.makedirs(

        OUTPUT_DIR,

        exist_ok=True
    )

    image = cv2.imread(
        image_path
    )

    candidates = detect_tool_candidates(
        image_path
    )

    print(
        f"[DEBUG] candidates="
        f"{len(candidates)}"
    )

    for index, candidate in enumerate(candidates):

        crop = image[

            candidate.y:
            candidate.y + candidate.height,

            candidate.x:
            candidate.x + candidate.width
        ]

        if crop.size == 0:

            continue

        output_path = (

            f"{OUTPUT_DIR}/"
            f"candidate_{index}.png"
        )

        cv2.imwrite(

            output_path,

            crop
        )

        print(
            f"[EXPORTED] "
            f"{output_path}"
        )