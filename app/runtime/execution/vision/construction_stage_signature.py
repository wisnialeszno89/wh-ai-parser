from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass(frozen=True, slots=True)
class ConstructionStageSignature:
    width: int
    height: int
    mean_gray: float
    std_gray: float
    edge_density: float
    dark_ratio: float
    mid_ratio: float
    strong_edge_ratio: float
    horizontal_energy: float
    vertical_energy: float


class ConstructionStageSignatureExtractor:
    """Extract a normalized, geometry-oriented fingerprint from a workspace crop."""

    def extract(self, crop: np.ndarray) -> ConstructionStageSignature:
        if crop is None or crop.size == 0:
            raise ValueError("Cannot extract signature from an empty crop")

        gray = cv2.cvtColor(crop, cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(gray, 40, 120)

        edge_density = float(np.count_nonzero(edges)) / float(edges.size)
        dark_ratio = float(np.count_nonzero(gray < 220)) / float(gray.size)
        mid_ratio = float(np.count_nonzero((gray >= 220) & (gray < 245))) / float(gray.size)
        strong_edge_ratio = float(np.count_nonzero(edges > 0)) / float(edges.size)

        gx = np.abs(cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3))
        gy = np.abs(cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3))

        horizontal_energy = float(np.mean(gy))
        vertical_energy = float(np.mean(gx))

        return ConstructionStageSignature(
            width=int(crop.shape[1]),
            height=int(crop.shape[0]),
            mean_gray=float(np.mean(gray)),
            std_gray=float(np.std(gray)),
            edge_density=edge_density,
            dark_ratio=dark_ratio,
            mid_ratio=mid_ratio,
            strong_edge_ratio=strong_edge_ratio,
            horizontal_energy=horizontal_energy,
            vertical_energy=vertical_energy,
        )

    def distance(self, left: ConstructionStageSignature, right: ConstructionStageSignature) -> float:
        """Compare signatures without being dominated by image scale."""
        return float(
            abs(left.mean_gray - right.mean_gray) / 255.0
            + abs(left.std_gray - right.std_gray) / 255.0
            + abs(left.edge_density - right.edge_density) * 8.0
            + abs(left.dark_ratio - right.dark_ratio) * 4.0
            + abs(left.mid_ratio - right.mid_ratio) * 4.0
            + abs(left.horizontal_energy - right.horizontal_energy) / 40.0
            + abs(left.vertical_energy - right.vertical_energy) / 40.0
        )
