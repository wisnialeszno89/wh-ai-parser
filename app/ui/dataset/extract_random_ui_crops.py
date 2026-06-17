import os
import cv2
import random


OUTPUT_DIR = (
    "outputs/random_ui_crops"
)


CROP_SIZE = 64

TOTAL_CROPS = 500


def extract_random_ui_crops(

    image_path: str
):

    image = cv2.imread(
        image_path
    )

    height, width, _ = image.shape

    os.makedirs(

        OUTPUT_DIR,

        exist_ok=True
    )

    for i in range(

        TOTAL_CROPS
    ):

        x = random.randint(

            0,

            width - CROP_SIZE
        )

        y = random.randint(

            0,

            height - CROP_SIZE
        )

        crop = image[

            y:y + CROP_SIZE,

            x:x + CROP_SIZE
        ]

        output_path = (

            f"{OUTPUT_DIR}/"
            f"crop_{i}.png"
        )

        cv2.imwrite(

            output_path,

            crop
        )

        print(
            f"[CROP] {output_path}"
        )

    print(
        f"[DONE] {TOTAL_CROPS}"
    )