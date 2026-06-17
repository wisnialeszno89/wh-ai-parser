import cv2

from app.ui.extractors.extract_toolbar import (
    extract_toolbar
)

from app.ui.extractors.extract_tools import (
    extract_tools
)


def render_tool_matches(

    image_path: str,

    output_path: str
):

    image = cv2.imread(
        image_path
    )

    toolbar = extract_toolbar(
        image_path
    )[0]

    tools = extract_tools(

        image_path,

        toolbar
    )

    cv2.rectangle(

        image,

        (toolbar.x, toolbar.y),

        (
            toolbar.x + toolbar.width,

            toolbar.y + toolbar.height
        ),

        (255, 0, 0),

        2
    )

    for tool in tools:

        cv2.rectangle(

            image,

            (tool.x, tool.y),

            (
                tool.x + tool.width,

                tool.y + tool.height
            ),

            (0, 0, 255),

            2
        )

        cv2.putText(

            image,

            tool.label,

            (tool.x, tool.y - 5),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.5,

            (0, 255, 0),

            1
        )

    cv2.imwrite(
        output_path,
        image
    )

    print(
        f"[DEBUG] saved: {output_path}"
    )