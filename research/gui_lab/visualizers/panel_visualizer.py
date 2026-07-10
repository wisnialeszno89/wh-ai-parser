import cv2

from research.gui_lab.core.panel_detector import (
    detect_panels,
)

INPUT = "research/gui_lab/input/windowhub.png"
OUTPUT = "research/gui_lab/output/panels_detected.png"


def main():

    image = cv2.imread(INPUT)

    if image is None:
        raise FileNotFoundError(INPUT)

    panels = detect_panels(image)

    debug = image.copy()

    print()
    print("========== DETECTED PANELS ==========")

    for index, panel in enumerate(panels, start=1):

        cv2.rectangle(
            debug,
            (panel.x, panel.y),
            (
                panel.x + panel.width,
                panel.y + panel.height,
            ),
            (0, 255, 0),
            2,
        )

        cv2.putText(
            debug,
            str(index),
            (
                panel.x + 5,
                panel.y + 20,
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 0, 255),
            2,
        )

        print(
            f"{index:02d} "
            f"x={panel.x:<4} "
            f"y={panel.y:<4} "
            f"w={panel.width:<4} "
            f"h={panel.height:<4}"
        )

    cv2.imwrite(
        OUTPUT,
        debug,
    )

    print()
    print(f"Detected: {len(panels)}")
    print(f"Saved: {OUTPUT}")


if __name__ == "__main__":
    main()