import cv2
import numpy as np


def detect_vertical_toolbar(

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

    column_scores = []

    SEARCH_WIDTH = 250

    for x in range(SEARCH_WIDTH):

        column = edges[:, x:x + 1]

        score = np.sum(
            column > 0
        )

        column_scores.append({

            "x": x,
            "score": score
        })

    column_scores = sorted(

        column_scores,

        key=lambda c: c["score"],

        reverse=True
    )

    best = column_scores[0]

    toolbar_x = best["x"] - 30

    print(
        f"[VERTICAL TOOLBAR X] "
        f"{toolbar_x}"
    )

    debug = image.copy()

    cv2.rectangle(

        debug,

        (max(0, toolbar_x - 30), 0),

        (min(width, toolbar_x + 30), height),

        (0, 255, 0),

        2
    )

    output_path = (
        "outputs/debug_vertical_toolbar.png"
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

        "x": toolbar_x,

        "width": 80
    }