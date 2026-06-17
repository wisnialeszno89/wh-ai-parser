import cv2

from app.ui.detection.detect_tool_candidates import (
    detect_tool_candidates
)


def render_tool_candidates(

    image_path: str,

    output_path: str
):

    image = cv2.imread(
        image_path
    )

    objects = detect_tool_candidates(
        image_path
    )

    for obj in objects:

        cv2.rectangle(

            image,

            (obj.x, obj.y),

            (
                obj.x + obj.width,

                obj.y + obj.height
            ),

            (0, 0, 255),

            2
        )

    cv2.imwrite(
        output_path,
        image
    )

    print(
        f"[DEBUG] saved: "
        f"{output_path}"
    )