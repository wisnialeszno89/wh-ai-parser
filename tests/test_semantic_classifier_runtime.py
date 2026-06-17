from app.ui.ml.semantic_classifier import (
    SemanticClassifier
)

import cv2


classifier = SemanticClassifier()

image = cv2.imread(
    "outputs/toolbar_slots/slot_22.png"
)

tool, confidence = (
    classifier.predict_crop(
        image
    )
)

print()
print(tool)
print(confidence)
print()