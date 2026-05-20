import cv2


def enhance_technical_drawing(
    image_path: str,
    output_path: str
):

    image = cv2.imread(
        image_path
    )

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    enhanced = cv2.GaussianBlur(
        gray,
        (3, 3),
        0
    )

    enhanced = cv2.equalizeHist(
        enhanced
    )

    cv2.imwrite(
        output_path,
        enhanced
    )

    return output_path