import cv2

IMAGE = "samples/geometry_region.jpg"

image = cv2.imread(
    IMAGE
)

gray = cv2.cvtColor(
    image,
    cv2.COLOR_BGR2GRAY
)

_, thresh = cv2.threshold(
    gray,
    140,
    255,
    cv2.THRESH_BINARY_INV
)

vertical_kernel = cv2.getStructuringElement(
    cv2.MORPH_RECT,
    (5, 120)
)

detected = cv2.morphologyEx(
    thresh,
    cv2.MORPH_OPEN,
    vertical_kernel
)

contours, _ = cv2.findContours(

    detected,

    cv2.RETR_EXTERNAL,

    cv2.CHAIN_APPROX_SIMPLE
)

for cnt in contours:

    x, y, w, h = cv2.boundingRect(cnt)

    cv2.rectangle(

        image,

        (x, y),

        (x + w, y + h),

        (0, 0, 255),

        2
    )

output = "app/vision/debug/contours_debug.jpg"

cv2.imwrite(
    output,
    image
)

print(output)