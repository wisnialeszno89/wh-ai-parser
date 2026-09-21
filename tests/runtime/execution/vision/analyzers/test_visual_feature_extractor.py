from __future__ import annotations

import cv2
import numpy as np

from app.runtime.execution.vision.analyzers.visual_feature_extractor import (
    VisualFeatureExtractor,
)
from app.runtime.execution.vision.models.rect import Rect


def test_uniform_bright_region_has_no_edges_and_is_bright() -> None:
    image = np.full((40, 40), 255, dtype=np.uint8)
    rect = Rect(x=0, y=0, width=40, height=40)

    features = VisualFeatureExtractor().extract(image, rect)

    assert features.edge_density == 0.0
    assert features.contour_density == 0.0
    assert features.dark_pixel_ratio == 0.0
    assert features.bright_pixel_ratio == 1.0


def test_uniform_dark_region_is_dark() -> None:
    image = np.zeros((40, 40), dtype=np.uint8)
    rect = Rect(x=0, y=0, width=40, height=40)

    features = VisualFeatureExtractor().extract(image, rect)

    assert features.edge_density == 0.0
    assert features.contour_density == 0.0
    assert features.dark_pixel_ratio == 1.0
    assert features.bright_pixel_ratio == 0.0


def test_rectangle_produces_edge_evidence() -> None:
    image = np.full((60, 60), 255, dtype=np.uint8)
    cv2.rectangle(image, (15, 15), (44, 44), 0, 2)

    rect = Rect(x=0, y=0, width=60, height=60)

    features = VisualFeatureExtractor().extract(image, rect)

    assert features.edge_density > 0.0
    assert features.dark_pixel_ratio > 0.0
    assert features.bright_pixel_ratio > 0.0


def test_color_image_is_supported() -> None:
    image = np.full((40, 40, 3), 255, dtype=np.uint8)
    image[10:30, 10:30] = (0, 0, 0)

    rect = Rect(x=0, y=0, width=40, height=40)

    features = VisualFeatureExtractor().extract(image, rect)

    assert features.dark_pixel_ratio > 0.0
    assert features.bright_pixel_ratio > 0.0

def test_interior_content_density_distinguishes_empty_and_content_regions() -> None:
    empty = np.full((40, 40), 255, dtype=np.uint8)

    content = empty.copy()
    cv2.rectangle(content, (10, 10), (29, 29), 0, -1)

    rect = Rect(x=0, y=0, width=40, height=40)

    extractor = VisualFeatureExtractor()

    empty_features = extractor.extract(empty, rect)
    content_features = extractor.extract(content, rect)

    assert content_features.interior_content_density > empty_features.interior_content_density


def test_border_edge_density_detects_border_near_candidate_boundary() -> None:
    image = np.full((60, 60), 255, dtype=np.uint8)
    cv2.rectangle(image, (1, 1), (58, 58), 0, 2)

    rect = Rect(x=0, y=0, width=60, height=60)

    features = VisualFeatureExtractor().extract(image, rect)

    assert features.border_edge_density > 0.0


def test_horizontal_and_vertical_edge_density_detect_orientation() -> None:
    image = np.full((60, 60), 255, dtype=np.uint8)
    cv2.line(image, (10, 30), (49, 30), 0, 2)

    rect = Rect(x=0, y=0, width=60, height=60)

    features = VisualFeatureExtractor().extract(image, rect)

    assert features.horizontal_edge_density > features.vertical_edge_density
