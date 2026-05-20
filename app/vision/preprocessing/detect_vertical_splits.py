import cv2
import numpy as np


def group_positions(
    positions,
    tolerance=20
):

    if not positions:
        return []

    groups = []

    current = [positions[0]]

    for p in positions[1:]:

        if p - current[-1] <= tolerance:

            current.append(p)

        else:

            groups.append(current)

            current = [p]

    groups.append(current)

    centers = []

    for g in groups:

        centers.append(
            int(sum(g) / len(g))
        )

    return centers


def detect_vertical_splits(
    image_path: str
):

    image = cv2.imread(
        image_path
    )

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    height, width = gray.shape

    darkness = []

    for x in range(width):

        column = gray[:, x]

        mean_value = np.mean(
            column
        )

        darkness.append(
            255 - mean_value
        )

    threshold = np.mean(
        darkness
    ) * 1.25

    candidates = []

    for x, value in enumerate(darkness):

        if value > threshold:

            candidates.append(x)

    grouped = group_positions(
        candidates
    )

    filtered = []

    last = None

    for g in grouped:

        if not (
            width * 0.30
            < g
            < width * 0.70
        ):
            continue

        if last is not None:

            gap = abs(g - last)

            if gap < width * 0.18:
                continue

        filtered.append(g)

        last = g

    return filtered