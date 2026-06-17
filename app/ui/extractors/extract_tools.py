import cv2

from app.ui.models.ui_object import (
    UIObject
)


TOOLS = {

    "frame_tool":

        "templates/frame_tool.png",

    "sash_tool":

        "templates/sash_tool.png",

    "glass_tool":

        "templates/glass_tool.png"
}


THRESHOLD = 0.5


def extract_tools(

    image_path: str,

    toolbar
):

    image = cv2.imread(
        image_path
    )

    toolbar_crop = image[

        toolbar.y:
        toolbar.y + toolbar.height,

        toolbar.x:
        toolbar.x + toolbar.width
    ]

    objects = []

    for tool_name, template_path in TOOLS.items():

        template = cv2.imread(
            template_path
        )

        if template is None:

            print(
                f"[ERROR] missing template: "
                f"{template_path}"
            )

            continue
            
        result = cv2.matchTemplate(

            toolbar_crop,

            template,

            cv2.TM_CCOEFF_NORMED
        )

        _, max_val, _, max_loc = cv2.minMaxLoc(
            result
        )

        print(
            f"[DEBUG] {tool_name} "
            f"confidence={max_val}"
        )

        if max_val < THRESHOLD:

            continue

        h, w = template.shape[:2]

        objects.append(

            UIObject(

                id=tool_name,

                object_type="tool",

                x=toolbar.x + max_loc[0],

                y=toolbar.y + max_loc[1],

                width=w,

                height=h,

                label=tool_name
            )
        )

    return objects