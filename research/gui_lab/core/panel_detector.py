from dataclasses import dataclass

import cv2


@dataclass(slots=True)
class Panel:

    x: int
    y: int
    width: int
    height: int


def detect_panels(image) -> list[Panel]:

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY,
    )

    binary = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        31,
        8,
    )

    horizontal_kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (80, 1),
    )

    horizontal = cv2.morphologyEx(
        binary,
        cv2.MORPH_OPEN,
        horizontal_kernel,
    )

    vertical_kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (1, 80),
    )

    vertical = cv2.morphologyEx(
        binary,
        cv2.MORPH_OPEN,
        vertical_kernel,
    )

    layout = cv2.bitwise_or(
        horizontal,
        vertical,
    )

    kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (5, 5),
    )

    layout = cv2.dilate(
        layout,
        kernel,
        iterations=2,
    )

    contours, _ = cv2.findContours(
        layout,
        cv2.RETR_TREE,
        cv2.CHAIN_APPROX_SIMPLE,
    )

    panels = []

    for contour in contours:

        x, y, w, h = cv2.boundingRect(
            contour,
        )

        area = w * h

        if area < 15000:
            continue

        if area > image.shape[0] * image.shape[1] * 0.95:
            continue

        panels.append(
            Panel(
                x=x,
                y=y,
                width=w,
                height=h,
            )
        )

    panels.sort(
        key=lambda p: (p.y, p.x)
    )

    return panels