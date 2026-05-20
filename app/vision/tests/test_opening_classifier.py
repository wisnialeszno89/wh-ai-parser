from app.vision.classifiers.opening_classifier import (
    classify_opening
)

result = classify_opening(
    "app/vision/debug/segments/segment_0_enhanced.jpg"
)

print(result)