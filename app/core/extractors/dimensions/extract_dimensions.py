from app.core.scene.models.scene_object import (
    SceneObject
)

from app.core.extractors.dimensions.detect_dimension_regions import (
    detect_dimension_regions
)


MIN_DIMENSION_WIDTH = 30
MIN_DIMENSION_HEIGHT = 15


def extract_dimensions(

    image_path: str,

    frame
):

    regions = detect_dimension_regions(
        image_path
    )

    dimensions = []

    for index, region in enumerate(regions):

        x, y, w, h = region

        if w < MIN_DIMENSION_WIDTH:
            continue

        if h < MIN_DIMENSION_HEIGHT:
            continue

        center_x = x + (w / 2)

        center_y = y + (h / 2)

        is_above = (
            center_y < frame.y
        )

        is_left = (
            center_x < frame.x
        )

        if not is_above and not is_left:

            continue

        orientation = "horizontal"

        if h > w:

            orientation = "vertical"

        dimensions.append(

            SceneObject(

                id=f"dimension_{index}",

                object_type="dimension",

                x=x,
                y=y,

                width=w,
                height=h,

                label="?",

                orientation=orientation
            )
        )

    return dimensions