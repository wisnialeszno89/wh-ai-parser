import cv2


IMAGE = "samples/wh_toolbar.png"

image = cv2.imread(
    IMAGE
)


clicks = []


def on_mouse(

    event,

    x,

    y,

    flags,

    param
):

    global clicks

    if event == cv2.EVENT_LBUTTONDOWN:

        clicks.append((x, y))

        print(f"[CLICK] {x}, {y}")

        if len(clicks) == 2:

            x1, y1 = clicks[0]
            x2, y2 = clicks[1]

            crop = image[
                min(y1, y2):max(y1, y2),
                min(x1, x2):max(x1, x2)
            ]

            output = "templates/custom_tool.png"

            cv2.imwrite(
                output,
                crop
            )

            print(
                f"[SAVED] {output}"
            )

            clicks = []


cv2.namedWindow(
    "cropper"
)

cv2.setMouseCallback(

    "cropper",

    on_mouse
)

while True:

    preview = image.copy()

    cv2.imshow(
        "cropper",
        preview
    )

    key = cv2.waitKey(1)

    if key == 27:
        break

cv2.destroyAllWindows()