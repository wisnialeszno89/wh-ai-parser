import cv2
import numpy as np
from dataclasses import dataclass


@dataclass(slots=True)
class PanelFingerprint:

    width: int
    height: int

    aspect_ratio: float

    edge_density: float

    white_ratio: float

    horizontal_density: float

    vertical_density: float


def build_fingerprint(panel_image):

    gray = cv2.cvtColor(
        panel_image,
        cv2.COLOR_BGR2GRAY,
    )

    h, w = gray.shape

    edges = cv2.Canny(
        gray,
        50,
        150,
    )

    edge_density = (
        np.count_nonzero(edges)
        / edges.size
    )

    white_ratio = (
        np.count_nonzero(gray > 220)
        / gray.size
    )

    horizontal_kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (40, 1),
    )

    vertical_kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (1, 40),
    )

    horizontal = cv2.morphologyEx(
        edges,
        cv2.MORPH_OPEN,
        horizontal_kernel,
    )

    vertical = cv2.morphologyEx(
        edges,
        cv2.MORPH_OPEN,
        vertical_kernel,
    )

    horizontal_density = (
        np.count_nonzero(horizontal)
        / horizontal.size
    )

    vertical_density = (
        np.count_nonzero(vertical)
        / vertical.size
    )

    return PanelFingerprint(
        width=w,
        height=h,
        aspect_ratio=w / h,
        edge_density=edge_density,
        white_ratio=white_ratio,
        horizontal_density=horizontal_density,
        vertical_density=vertical_density,
    )