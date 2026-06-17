import cv2
import numpy as np


def detect_toolbar_band(

    image_path: str
):

    image = cv2.imread(
        image_path
    )

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    edges = cv2.Canny(
        gray,
        80,
        160
    )

    height, width = edges.shape

    row_scores = []

    for y in range(height):

        row = edges[y:y + 1, :]

        score = np.sum(row > 0)

        row_scores.append({

            "y": y,
            "score": score
        })

    row_scores = sorted(

        row_scores,

        key=lambda r: r["score"],

        reverse=True
    )

    best = row_scores[0]

    toolbar_y = best["y"]

    print(
        f"[TOOLBAR Y] "
        f"{toolbar_y}"
    )

    debug = image.copy()

    cv2.rectangle(

        debug,

        (0, max(0, toolbar_y - 40)),

        (width, min(height, toolbar_y + 40)),

        (0, 255, 0),

        2
    )

    output_path = (
        "outputs/debug_toolbar_band.png"
    )

    cv2.imwrite(
        output_path,
        debug
    )

    print(
        f"[SAVED] "
        f"{output_path}"
    )

    return {

        "y": toolbar_y,

        "height": 80
    }