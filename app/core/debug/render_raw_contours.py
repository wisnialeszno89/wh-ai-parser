import cv2

from app.core.extractors.dimensions.detect_dimension_regions import (
    detect_dimension_regions
)


def render_raw_contours(

    image_path: str,

    output_path: str
):

    image = cv2.imread(
        image_path
    )

    regions = detect_dimension_regions(
        image_path
    )

    for index, region in enumerate(regions):

        x, y, w, h = region

        cv2.rectangle(

            image,

            (x, y),

            (x + w, y + h),

            (0, 0, 255),

            2
        )

        cv2.putText(

            image,

            str(index),

            (x, y - 5),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.5,

            (255, 0, 0),

            1
        )

    cv2.imwrite(
        output_path,
        image
    )

    print(
        f"[DEBUG] saved: {output_path}"
    )