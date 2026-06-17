import os
import cv2

from app.ui.dataset.extract_icon_candidates import (
    extract_icon_candidates
)


OUTPUT_DIR = (
    "dataset_augmented/non_icon"
)


def build_hard_negative_dataset(
    image_path: str
):

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    candidates = (
        extract_icon_candidates(
            image_path
        )
    )

    saved = 0

    for candidate in candidates:

        crop = candidate["crop"]

        output_path = (
            f"{OUTPUT_DIR}/"
            f"hard_negative_{saved}.png"
        )

        cv2.imwrite(
            output_path,
            crop
        )

        saved += 1

    print(
        f"[SAVED] {saved}"
    )


if __name__ == "__main__":

    build_hard_negative_dataset(
        "samples/zapytanie1.jpg"
    )