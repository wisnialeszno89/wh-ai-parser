import cv2

from app.vision.preprocessing.detect_diagonals import (
    detect_diagonals
)

IMAGE = "app/vision/debug/segments/segment_0_enhanced.jpg"

image = cv2.imread(
    IMAGE
)

diagonals = detect_diagonals(
    IMAGE
)

print("\nDIAGONALS:\n")

for idx, d in enumerate(diagonals):

    x1, y1, x2, y2 = d

    length = (
        (x2 - x1) ** 2
        + (y2 - y1) ** 2
    ) ** 0.5

    print(
        f"{idx}:",
        d,
        "length=",
        round(length, 2)
    )

    cv2.putText(

        image,

        str(idx),

        (x1, y1),

        cv2.FONT_HERSHEY_SIMPLEX,

        1,

        (0, 255, 0),

        2
    )

    cv2.line(

        image,

        (x1, y1),

        (x2, y2),

        (0, 0, 255),

        2
    )

output = "app/vision/debug/diagonals_debug.jpg"

cv2.imwrite(
    output,
    image
)

print("\nOUTPUT:")
print(output)