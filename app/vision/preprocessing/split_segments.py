import os

import cv2

from app.vision.preprocessing.detect_vertical_splits import (
    detect_vertical_splits
)


def split_segments(
    image_path: str,
    output_dir: str = "app/vision/debug/segments"
):

    os.makedirs(
        output_dir,
        exist_ok=True
    )

    image = cv2.imread(
        image_path
    )

    height, width = image.shape[:2]

    splits = detect_vertical_splits(
        image_path
    )

    boundaries = [0]

    boundaries.extend(splits)

    boundaries.append(width)

    segment_paths = []

    padding = 20

    for i in range(
        len(boundaries) - 1
    ):

        left = max(
            0,
            boundaries[i] - padding
        )

        right = min(
            width,
            boundaries[i + 1] + padding
        )

        segment = image[
            :,
            left:right
        ]

        output_path = (
            f"{output_dir}/segment_{i}.jpg"
        )

        cv2.imwrite(
            output_path,
            segment
        )

        segment_paths.append(
            output_path
        )

    return segment_paths