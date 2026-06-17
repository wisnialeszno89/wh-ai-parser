import cv2

from app.ui.extractors.extract_toolbar import (
    extract_toolbar
)


def render_toolbar_debug(

    image_path: str,

    output_path: str
):

    image = cv2.imread(
        image_path
    )

    toolbars = extract_toolbar(
        image_path
    )

    for toolbar in toolbars:

        cv2.rectangle(

            image,

            (toolbar.x, toolbar.y),

            (
                toolbar.x + toolbar.width,

                toolbar.y + toolbar.height
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