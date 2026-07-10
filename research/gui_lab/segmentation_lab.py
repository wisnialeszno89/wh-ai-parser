import cv2
import math

INPUT = "research/gui_lab/input/windowhub.png"
OUTPUT = "research/gui_lab/output/lines.png"


def main():

    image = cv2.imread(INPUT)

    if image is None:
        raise FileNotFoundError(
            f"Cannot load image: {INPUT}"
        )

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY,
    )

    #
    # Edge detection
    #

    edges = cv2.Canny(
        gray,
        50,
        150,
    )

    #
    # Detect lines
    #

    lines = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=math.pi / 180,
        threshold=80,
        minLineLength=100,
        maxLineGap=5,
    )

    debug = image.copy()

    count = 0

    if lines is not None:

        for line in lines:

            x1, y1, x2, y2 = line[0]

            cv2.line(
                debug,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2,
            )

            count += 1

    cv2.imwrite(
        OUTPUT,
        debug,
    )

    print()
    print(f"Detected lines: {count}")
    print(f"Saved: {OUTPUT}")


if __name__ == "__main__":
    main()