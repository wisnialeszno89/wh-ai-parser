import cv2

from app.ui.models.ui_object import (
    UIObject
)


def extract_toolbar(

    image_path: str
):

    image = cv2.imread(
        image_path
    )

    height, width = image.shape[:2]

    objects = []

    objects.append(

        UIObject(

            id="toolbar_main",

            object_type="toolbar",

            x=0,
            y=0,

            width=width,

            height=55,

            label="main"
        )
    )

    objects.append(

        UIObject(

            id="toolbar_actions",

            object_type="toolbar",

            x=0,
            y=55,

            width=width,

            height=80,

            label="actions"
        )
    )

    return objects