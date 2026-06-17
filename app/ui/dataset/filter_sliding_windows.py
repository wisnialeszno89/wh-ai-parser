import os
import cv2
import numpy as np


INPUT_DIR = "outputs/sliding_candidates"

OUTPUT_DIR = "outputs/filtered_candidates"


MIN_STDDEV = 25


def filter_sliding_windows():

    os.makedirs(

        OUTPUT_DIR,

        exist_ok=True
    )

    files = os.listdir(
        INPUT_DIR
    )

    kept = 0

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

        gray = cv2.cvtColor(

            image,

            cv2.COLOR_BGR2GRAY
        )

        stddev = np.std(
            gray
        )

        if stddev < MIN_STDDEV:

            continue

        output_path = (

            f"{OUTPUT_DIR}/"
            f"{filename}"
        )

        cv2.imwrite(

            output_path,

            image
        )

        kept += 1

    print(
        f"[FILTERED] kept="
        f"{kept}"
    )