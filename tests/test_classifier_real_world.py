import os
import cv2

from app.ui.ml.semantic_classifier import (
    SemanticClassifier
)


ICON_DIR = (
    "tmp/test_icons"
)

NON_ICON_DIR = (
    "tmp/test_non_icons"
)


classifier = (
    SemanticClassifier()
)


def evaluate_folder(

    folder_path: str,

    expected_type: str
):

    files = sorted(

        [
            f
            for f in os.listdir(
                folder_path
            )
            if f.endswith(".png")
        ]
    )

    print()
    print("=" * 80)
    print(expected_type.upper())
    print("=" * 80)

    total = 0

    for file_name in files:

        image_path = os.path.join(
            folder_path,
            file_name
        )

        image = cv2.imread(
            image_path
        )

        tool, confidence, top3 = (

            classifier.predict_crop(
                image
            )
        )

        print()

        print(
            f"{file_name}"
        )

        print(
            f"TOP1: "
            f"{tool} "
            f"{confidence:.6f}"
        )

        for item in top3:

            print(
                f"    "
                f"{item['tool']} "
                f"{item['confidence']:.6f}"
            )

        total += 1

    print()
    print(
        f"[FILES] {total}"
    )
    print()


evaluate_folder(

    ICON_DIR,

    "icons"
)

evaluate_folder(

    NON_ICON_DIR,

    "non_icons"
)