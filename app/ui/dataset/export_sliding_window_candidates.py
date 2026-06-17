import os
import cv2


OUTPUT_DIR = "outputs/sliding_candidates"

WINDOW_SIZE = 24
STEP = 8


def export_sliding_window_candidates(

    image_path: str
):

    os.makedirs(

        OUTPUT_DIR,

        exist_ok=True
    )

    image = cv2.imread(
        image_path
    )

    height, width = image.shape[:2]

    counter = 0

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

            crop = image[

                y:y + WINDOW_SIZE,

                x:x + WINDOW_SIZE
            ]

            output_path = (

                f"{OUTPUT_DIR}/"
                f"window_{counter}.png"
            )

            cv2.imwrite(

                output_path,

                crop
            )

            counter += 1

    print(
        f"[EXPORTED] windows="
        f"{counter}"
    )