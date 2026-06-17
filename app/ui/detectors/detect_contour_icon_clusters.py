import os
import cv2
import numpy as np


OUTPUT_PATH = (
    "outputs/debug_contour_clusters.png"
)


WINDOW_SIZE = 160

STEP = 48

TOP_K = 20


MIN_CONTOUR_AREA = 20
MAX_CONTOUR_AREA = 800


def detect_contour_icon_clusters(

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

    clusters = []

    for y in range(

        0,

        height - WINDOW_SIZE,

        STEP
    ):

        for x in range(

            0,

            width - WINDOW_SIZE,

            STEP
        ):

            crop = gray[

                y:y + WINDOW_SIZE,

                x:x + WINDOW_SIZE
            ]

            edges = cv2.Canny(

                crop,

                80,

                160
            )

            contours, _ = cv2.findContours(

                edges,

                cv2.RETR_LIST,

                cv2.CHAIN_APPROX_SIMPLE
            )

            small_objects = 0

            for contour in contours:

                area = cv2.contourArea(
                    contour
                )

                if (

                    MIN_CONTOUR_AREA

                    <= area

                    <= MAX_CONTOUR_AREA
                ):

                    small_objects += 1

            clusters.append({

                "x": x,

                "y": y,

                "score": small_objects
            })

    clusters = sorted(

        clusters,

        key=lambda c: c["score"],

        reverse=True
    )

    top_clusters = clusters[:TOP_K]

    debug = image.copy()

    for cluster in top_clusters:

        x = cluster["x"]

        y = cluster["y"]

        cv2.rectangle(

            debug,

            (x, y),

            (

                x + WINDOW_SIZE,

                y + WINDOW_SIZE
            ),

            (0, 255, 0),

            2
        )

        print(

            f"[CONTOUR CLUSTER] "

            f"x={x} "

            f"y={y} "

            f"score={cluster['score']}"
        )

    os.makedirs(

        "outputs",

        exist_ok=True
    )

    cv2.imwrite(

        OUTPUT_PATH,

        debug
    )

    print(
        f"[SAVED] {OUTPUT_PATH}"
    )

    return top_clusters