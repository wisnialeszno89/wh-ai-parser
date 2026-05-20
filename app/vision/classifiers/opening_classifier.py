from app.vision.preprocessing.detect_diagonals import (
    detect_diagonals
)


def classify_opening(
    image_path: str
):

    diagonals = detect_diagonals(
        image_path
    )

    if not diagonals:
        return "FIX"

    positive = 0
    negative = 0

    for line in diagonals:

        x1, y1, x2, y2 = line

        dx = x2 - x1
        dy = y2 - y1

        if dx == 0:
            continue

        slope = dy / dx

        if slope > 0:
            positive += 1
        else:
            negative += 1

    if positive > 0 and negative > 0:
        return "RU"

    return "R"