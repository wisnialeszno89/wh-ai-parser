import cv2

from app.vision.preprocessing.detect_vertical_splits import (
    detect_vertical_splits
)

IMAGE_PATH = "samples/geometry_region.jpg"

image = cv2.imread(
    IMAGE_PATH
)

splits = detect_vertical_splits(
    IMAGE_PATH
)

for x in splits:

    cv2.line(
        image,
        (x, 0),
        (x, image.shape[0]),
        (0, 0, 255),
        3
    )

output = "app/vision/debug/vertical_debug.jpg"

cv2.imwrite(
    output,
    image
)

print(output)