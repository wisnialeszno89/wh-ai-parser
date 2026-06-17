import os
import cv2
import numpy as np


OUTPUT_DIR = "outputs/icon_candidates"

WINDOW_SIZE = 24
STEP = 8

MIN_EDGE_DENSITY = 0.08
MIN_STDDEV = 30

OVERLAP_DISTANCE = 16


def calculate_edge_density(

    edges
):

    edge_pixels = np.sum(
        edges > 0
    )

    total_pixels = edges.shape[0] * edges.shape[1]

    return edge_pixels / total_pixels


def is_overlapping(

    x1,
    y1,

    x2,
    y2
):

    return (

        abs(x1 - x2) < OVERLAP_DISTANCE
        and
        abs(y1 - y2) < OVERLAP_DISTANCE
    )


def export_icon_candidates(

    image_path: str
):

    os.makedirs(

        OUTPUT_DIR,

        exist_ok=True
    )

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

            stddev = np.std(
                crop
            )

            if stddev < MIN_STDDEV:

                continue

            edges = cv2.Canny(

                crop,

                80,

                160
            )

            edge_density = calculate_edge_density(
                edges
            )

            if edge_density < MIN_EDGE_DENSITY:

                continue

            score = (

                edge_density * 100
                +
                stddev
            )

            candidates.append({

                "x": x,
                "y": y,

                "crop": crop,

                "score": score
            })

    candidates = sorted(

        candidates,

        key=lambda c: c["score"],

        reverse=True
    )

    selected = []

    for candidate in candidates:

        overlap = False

        for existing in selected:

            if is_overlapping(

                candidate["x"],
                candidate["y"],

                existing["x"],
                existing["y"]
            ):

                overlap = True
                break

        if overlap:

            continue

        selected.append(
            candidate
        )

    for index, candidate in enumerate(selected):

        output_path = (

            f"{OUTPUT_DIR}/"
            f"icon_{index}.png"
        )

        cv2.imwrite(

            output_path,

            candidate["crop"]
        )

    print(
        f"[ICON CANDIDATES] kept="
        f"{len(selected)}"
    )