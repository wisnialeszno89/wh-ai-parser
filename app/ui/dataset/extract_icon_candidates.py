import os
import cv2
import numpy as np


OUTPUT_DIR = (
    "outputs/icon_candidates_v2"
)


WINDOW_SIZE = 64

STEP = 40

TOP_K = 150


MIN_OBJECTS = 2

MIN_CONTOUR_AREA = 20
MAX_CONTOUR_AREA = 800


def extract_icon_candidates(

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

    candidates = []

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

            square_objects = 0

            for contour in contours:

                area = cv2.contourArea(
                    contour
                )

                if not (

                    MIN_CONTOUR_AREA

                    <= area

                    <= MAX_CONTOUR_AREA
                ):

                    continue

                x2, y2, w2, h2 = cv2.boundingRect(
                    contour
                )

                ratio = w2 / max(h2, 1)

                if 0.6 <= ratio <= 1.4:

                    square_objects += 1

                small_objects += 1

            score = (

                small_objects
                +
                (square_objects * 2)
            )

            if small_objects < MIN_OBJECTS:
                continue

            candidates.append({

            "x": x,
            "y": y,

            "crop": image[
            y:y + WINDOW_SIZE,
            x:x + WINDOW_SIZE
        ],

    "score": score
})

    candidates = sorted(

        candidates,

        key=lambda c: c["score"],

        reverse=True
    )

    top_candidates = candidates[:TOP_K]

    os.makedirs(

        OUTPUT_DIR,

        exist_ok=True
    )

    debug = image.copy()

    for index, candidate in enumerate(

        top_candidates
    ):

        x = candidate["x"]

        y = candidate["y"]

        crop = image[

            y:y + WINDOW_SIZE,

            x:x + WINDOW_SIZE
        ]

        output_path = (

            f"{OUTPUT_DIR}/"
            f"candidate_{index}.png"
        )

        cv2.imwrite(

            output_path,

            crop
        )

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

            f"[ICON CANDIDATE] "

            f"{candidate['score']} "

            f"x={x} "

            f"y={y}"
        )

    cv2.imwrite(

        "outputs/debug_icon_candidates.png",

        debug
    )

    print(
        f"[DONE] {len(top_candidates)}"
    )
    return top_candidates