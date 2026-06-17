import os
import cv2
from collections import Counter

from app.ui.ml.semantic_classifier_v3 import (
    SemanticClassifierV3
)


FOLDER = (
    "tmp/test_icons"
)


classifier = (
    SemanticClassifierV3()
)

counter = Counter()

files = sorted(

    [
        f
        for f in os.listdir(
            FOLDER
        )
        if f.endswith(".png")
    ]
)

for file_name in files:

    image = cv2.imread(

        os.path.join(
            FOLDER,
            file_name
        )
    )

    tool, confidence, top3 = (

        classifier.predict_crop(
            image
        )
    )

    counter[tool] += 1

    print()

    print(
        file_name
    )

    print(
        f"{tool} "
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