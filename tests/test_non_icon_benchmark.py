import os
import cv2
from collections import Counter

from app.ui.ml.semantic_classifier import (
    SemanticClassifier
)

FOLDERS = [

    "outputs/non_icon",

    "tmp/test_non_icons"
]

classifier = (
    SemanticClassifier()
)

counter = Counter()

for folder in FOLDERS:

    print()
    print("=" * 80)
    print(folder)
    print("=" * 80)

    files = sorted(

        [
            f
            for f in os.listdir(folder)
            if f.endswith(".png")
        ]
    )

    for file_name in files:

        image = cv2.imread(

            os.path.join(
                folder,
                file_name
            )
        )

        tool, confidence, top3 = (

            classifier.predict_crop(
                image
            )
        )

        counter[tool] += 1

        print(
            f"{file_name:<25}"
            f"{tool:<25}"
            f"{confidence:.4f}"
        )

print()
print("=" * 80)
print("SUMMARY")
print("=" * 80)

for tool, count in counter.most_common():

    print(
        f"{tool:<30}"
        f"{count}"
    )