import os
import cv2


WINDOW_SIZE = 96


def save_toolbar_context(

    image_path: str,

    x: int,
    y: int,

    label: str,

    output_name: str
):

    image = cv2.imread(
        image_path
    )

    height, width = image.shape[:2]

    x1 = max(
        0,
        x - WINDOW_SIZE // 2
    )

    y1 = max(
        0,
        y - WINDOW_SIZE // 2
    )

    x2 = min(
        width,
        x1 + WINDOW_SIZE
    )

    y2 = min(
        height,
        y1 + WINDOW_SIZE
    )

    crop = image[
        y1:y2,
        x1:x2
    ]

    output_dir = (
        f"dataset/{label}"
    )

    os.makedirs(
        output_dir,
        exist_ok=True
    )

    output_path = (
        f"{output_dir}/"
        f"{output_name}.png"
    )

    cv2.imwrite(
        output_path,
        crop
    )

    print(
        f"[SAVED] "
        f"{output_path}"
    )