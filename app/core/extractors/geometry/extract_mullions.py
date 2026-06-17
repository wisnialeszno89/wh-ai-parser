from app.core.scene.models.scene_object import (
    SceneObject
)

from app.vision.preprocessing.detect_vertical_splits import (
    detect_vertical_splits
)


def extract_mullions(

    image_path: str,

    frame
):

    splits = detect_vertical_splits(
        image_path
    )

    objects = []

    for index, x in enumerate(splits):

        if x <= frame.x:

            continue

        if x >= frame.x + frame.width:

            continue

        objects.append(

            SceneObject(

                id=f"mullion_{index}",

                object_type="mullion",

                x=x,

                y=frame.y,

                width=10,

                height=frame.height
            )
        )

    return objects