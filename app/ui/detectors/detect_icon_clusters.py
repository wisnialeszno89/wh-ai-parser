import os
import cv2
import numpy as np


OUTPUT_PATH = (
    "outputs/debug_icon_clusters.png"
)


WINDOW_SIZE = 96

STEP = 32

TOP_K = 20


def detect_icon_clusters(

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

            edge_density = (

                np.sum(edges > 0)
                /
                (WINDOW_SIZE * WINDOW_SIZE)
            )

            clusters.append({

                "x": x,

                "y": y,

                "score": edge_density
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

            f"[ICON CLUSTER] "

            f"x={x} "

            f"y={y} "

            f"score={cluster['score']:.4f}"
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