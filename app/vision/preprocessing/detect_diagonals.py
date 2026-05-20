import cv2
import numpy as np


def detect_diagonals(
    image_path: str
):

    image = cv2.imread(image_path)

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    edges = cv2.Canny(
        gray,
        50,
        150
    )

    lines = cv2.HoughLinesP(

        edges,

        1,

        np.pi / 180,

        threshold=40,

        minLineLength=40,

        maxLineGap=10
    )

    diagonals = []

    if lines is None:
        return diagonals

    center_x = image.shape[1] / 2
    center_y = image.shape[0] / 2

    for line in lines:

        x1, y1, x2, y2 = line[0]

        dx = abs(x2 - x1)
        dy = abs(y2 - y1)

        if dx == 0:
            continue

        slope = dy / dx

        line_center_x = (x1 + x2) / 2
        line_center_y = (y1 + y2) / 2

        distance_x = abs(
            line_center_x - center_x
        )

        distance_y = abs(
            line_center_y - center_y
        )

        if (
            0.5 < slope < 2.5
            and distance_x < image.shape[1] * 0.35
            and distance_y < image.shape[0] * 0.20
        ):

            length = (
                (x2 - x1) ** 2
                + (y2 - y1) ** 2
            ) ** 0.5

            if length > image.shape[1] * 0.35:

                diagonals.append(
                    (x1, y1, x2, y2)
                )

    return diagonals