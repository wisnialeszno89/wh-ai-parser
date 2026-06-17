import os
import cv2
import math
import numpy as np


INPUT_DIR = "outputs/filtered_candidates"

OUTPUT_PATH = "outputs/candidate_grid.jpg"

THUMB_SIZE = 48

COLUMNS = 10


def build_candidate_grid():

    files = sorted(

        os.listdir(INPUT_DIR)
    )

    images = []

    for filename in files:

        path = (

            f"{INPUT_DIR}/"
            f"{filename}"
        )

        image = cv2.imread(
            path
        )

        if image is None:

            continue

        thumb = cv2.resize(

            image,

            (
                THUMB_SIZE,

                THUMB_SIZE
            )
        )

        images.append(
            thumb
        )

    rows = math.ceil(

        len(images) / COLUMNS
    )

    grid = np.zeros(

        (
            rows * THUMB_SIZE,

            COLUMNS * THUMB_SIZE,

            3
        ),

        dtype=np.uint8
    )

    for index, image in enumerate(images):

        row = index // COLUMNS
        col = index % COLUMNS

        y = row * THUMB_SIZE
        x = col * THUMB_SIZE

        grid[
            y:y + THUMB_SIZE,
            x:x + THUMB_SIZE
        ] = image

    cv2.imwrite(

        OUTPUT_PATH,

        grid
    )

    print(
        f"[GRID] saved: "
        f"{OUTPUT_PATH}"
    )