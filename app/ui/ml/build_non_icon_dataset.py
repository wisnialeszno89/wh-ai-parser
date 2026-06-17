import os
import cv2
import random


OUTPUT_DIR = (
    "dataset_iconness/non_icon"
)

CROP_SIZE = 64

TOTAL_CROPS = 200


def build_non_icon_dataset(

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

    saved = 0

    attempts = 0

    while (

        saved < TOTAL_CROPS

        and

        attempts < 5000
    ):

        attempts += 1

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

        gray = cv2.cvtColor(

            crop,

            cv2.COLOR_BGR2GRAY
        )

        edges = cv2.Canny(

            gray,

            80,

            160
        )

        edge_ratio = (

            (edges > 0).sum()
            /
            edges.size
        )

        if edge_ratio < 0.02:
            continue

        if edge_ratio > 0.15:
            continue

        output_path = (

            f"{OUTPUT_DIR}/"
            f"non_icon_{saved}.png"
        )

        cv2.imwrite(

            output_path,

            crop
        )

        saved += 1

    print(
        f"[GENERATED] {saved}"
    )


if __name__ == "__main__":

    build_non_icon_dataset(
        "samples/zmieniony_wh_screen.png"
    )