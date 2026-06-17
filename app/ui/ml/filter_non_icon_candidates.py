import os
import shutil
import cv2

from app.ui.ml.semantic_classifier import (
    SemanticClassifier
)


SOURCE_DIR = (
    "dataset_augmented/non_icon_v2"
)

REJECTED_DIR = (
    "dataset_augmented/rejected_non_icons"
)

ICON_THRESHOLD = 0.95


def main():

    os.makedirs(
        REJECTED_DIR,
        exist_ok=True
    )

    classifier = (
        SemanticClassifier()
    )

    moved = 0
    kept = 0

    files = [

        f

        for f in os.listdir(
            SOURCE_DIR
        )

        if f.endswith(".png")
    ]

    total = len(files)

    for index, file_name in enumerate(
        files,
        start=1
    ):

        path = os.path.join(
            SOURCE_DIR,
            file_name
        )

        image = cv2.imread(
            path
        )

        if image is None:
            continue

        tool, confidence, _ = (

            classifier.predict_crop(
                image
            )
        )

        if (

            tool != "non_icon"

            and

            confidence > ICON_THRESHOLD

        ):

            shutil.move(

                path,

                os.path.join(
                    REJECTED_DIR,
                    file_name
                )
            )

            moved += 1

        else:

            kept += 1

        if index % 100 == 0:

            print(

                f"[{index}/{total}] "

                f"kept={kept} "

                f"moved={moved}"
            )

    print()
    print(
        f"[KEPT] {kept}"
    )
    print(
        f"[REJECTED] {moved}"
    )
    print()


if __name__ == "__main__":
    main()