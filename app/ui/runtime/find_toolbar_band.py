import cv2
import numpy as np


WINDOW_W = 220
WINDOW_H = 600

STEP = 80

MIN_ICON_SIZE = 12
MAX_ICON_SIZE = 64

MIN_OBJECTS = 12


def find_toolbar_band(
    image
):

    gray = cv2.cvtColor(

        image,

        cv2.COLOR_BGR2GRAY
    )

    edges = cv2.Canny(

        gray,

        80,

        160
    )

    height, width = gray.shape

    regions = []

    debug = image.copy()

    for y in range(

        0,

        height - WINDOW_H,

        STEP
    ):

        for x in range(

            0,

            width - WINDOW_W,

            STEP
        ):

            roi = edges[

                y:y + WINDOW_H,

                x:x + WINDOW_W
            ]

            contours, _ = cv2.findContours(

                roi,

                cv2.RETR_LIST,

                cv2.CHAIN_APPROX_SIMPLE
            )

            icon_like = 0

            for contour in contours:

                x2, y2, w2, h2 = cv2.boundingRect(
                    contour
                )

                if not (
                    MIN_ICON_SIZE <= w2 <= MAX_ICON_SIZE
                ):
                    continue

                if not (
                    MIN_ICON_SIZE <= h2 <= MAX_ICON_SIZE
                ):
                    continue

                ratio = w2 / max(h2, 1)

                if not (
                    0.7 <= ratio <= 1.3
                ):
                    continue

                area = cv2.contourArea(
                    contour
                )

                if area < 40:
                    continue

                icon_like += 1

            if icon_like < MIN_OBJECTS:

                continue

            regions.append({

                "x": x,
                "y": y,

                "width": WINDOW_W,
                "height": WINDOW_H,

                "score": icon_like
            })

    regions = sorted(

        regions,

        key=lambda r: r["score"],

        reverse=True
    )

    top_regions = regions[:10]

    for region in top_regions:

        cv2.rectangle(

            debug,

            (
                region["x"],
                region["y"]
            ),

            (
                region["x"] +
                region["width"],

                region["y"] +
                region["height"]
            ),

            (0, 255, 0),

            3
        )

        print(
            f"[BAND] "
            f"score={region['score']} "
            f"x={region['x']} "
            f"y={region['y']}"
        )

    cv2.imwrite(

        "outputs/debug_toolbar_band.png",

        debug
    )

    print()

    print(
        f"[REGIONS] "
        f"{len(top_regions)}"
    )

    return top_regions