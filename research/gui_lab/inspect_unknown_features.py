from pathlib import Path

import cv2

from app.runtime.execution.vision.analyzers.candidate_features import CandidateFeatureExtractor
from app.runtime.execution.vision.analyzers.candidate_filter import CandidateFilter
from app.runtime.execution.vision.analyzers.structural_classifier_v2 import StructuralClassifierV2
from app.runtime.execution.vision.analyzers.visual_feature_extractor import VisualFeatureExtractor

IMAGE_PATH = Path("samples/wh_screen.png")


def main():
    image = cv2.imread(str(IMAGE_PATH))

    if image is None:
        raise RuntimeError(f"Could not load image: {IMAGE_PATH}")

    height, width = image.shape[:2]

    edges = cv2.Canny(image, 60, 150)

    contours, hierarchy = cv2.findContours(
        edges,
        cv2.RETR_TREE,
        cv2.CHAIN_APPROX_SIMPLE,
    )
    candidates = CandidateFilter().filter(contours, hierarchy=hierarchy, roi_width=width, roi_height=height)
    feature_extractor = CandidateFeatureExtractor()
    structural_features = feature_extractor.extract(candidates, roi_width=width, roi_height=height)
    classifications = StructuralClassifierV2().classify(structural_features)
    visual_extractor = VisualFeatureExtractor()
    rows = []

    for candidate, features, classification in zip(
        candidates,
        structural_features,
        classifications,
    ):
        visual = visual_extractor.extract(
            image,
            candidate.rect,
            contours=contours,
        )
        rows.append((candidate, features, classification, visual))

    print(f"TOTAL candidates: {len(rows)}")
    print("-" * 120)

    from collections import defaultdict

    grouped = defaultdict(list)

    for candidate, features, classification, visual in rows:
        grouped[classification.control_type.name].append(
            (candidate, features, visual)
        )

    for control_type in sorted(grouped):
        group = grouped[control_type]

        print()
        print(f"[{control_type}] count={len(group)}")

        edge = [row[2].edge_density for row in group]
        contour = [row[2].contour_density for row in group]
        children = [row[1].child_count for row in group]
        areas = [row[1].area_ratio for row in group]
        aspects = [row[1].aspect_ratio for row in group]

        print(
            f"  area_ratio:     min={min(areas):.4f} "
            f"mean={sum(areas)/len(areas):.4f} "
            f"max={max(areas):.4f}"
        )
        print(
            f"  aspect_ratio:   min={min(aspects):.2f} "
            f"mean={sum(aspects)/len(aspects):.2f} "
            f"max={max(aspects):.2f}"
        )
        print(
            f"  children:       min={min(children)} "
            f"mean={sum(children)/len(children):.2f} "
            f"max={max(children)}"
        )
        print(
            f"  edge_density:   min={min(edge):.4f} "
            f"mean={sum(edge)/len(edge):.4f} "
            f"max={max(edge):.4f}"
        )
        print(
            f"  contour_density:min={min(contour):.6f} "
            f"mean={sum(contour)/len(contour):.6f} "
            f"max={max(contour):.6f}"
        )

    print()
    print("=" * 120)
    print("POTENTIAL INTERACTIVE CANDIDATES")
    print("=" * 120)

    unknown = grouped.get("UNKNOWN", [])

    selected = [
        row for row in unknown
        if (
            row[1].area_ratio < 0.03
            and row[1].width >= 20
            and row[1].height >= 15
            and row[1].width <= 500
            and row[1].height <= 200
        )
    ]

    selected.sort(
        key=lambda row: (
            row[1].child_count > 0,
            row[2].edge_density,
            row[1].area_ratio,
        ),
        reverse=True,
    )

    print(f"selected: {len(selected)}")

    for index, (candidate, features, visual) in enumerate(selected[:40], start=1):
        rect = candidate.rect
        print(
            f"{index:02d} "
            f"{rect.width}x{rect.height} "
            f"area={features.area_ratio:.4f} "
            f"aspect={features.aspect_ratio:.2f} "
            f"depth={features.depth} "
            f"children={features.child_count} "
            f"siblings={features.sibling_count} "
            f"edge={visual.edge_density:.4f} "
            f"contour={visual.contour_density:.6f} "
            f"pos=({rect.x},{rect.y})"
        )

    print()
    print("=" * 120)
    print("LARGEST CANDIDATES PER CLASS")
    print("=" * 120)

    for control_type in sorted(grouped):
        group = sorted(
            grouped[control_type],
            key=lambda row: row[1].area,
            reverse=True,
        )

        print()
        print(f"[{control_type}]")

        for index, (candidate, features, visual) in enumerate(group[:5], start=1):
            rect = candidate.rect
            print(
                f"  {index:02d} "
                f"{rect.width}x{rect.height} "
                f"area={features.area_ratio:.4f} "
                f"aspect={features.aspect_ratio:.2f} "
                f"depth={features.depth} "
                f"children={features.child_count} "
                f"edge={visual.edge_density:.4f} "
                f"contour={visual.contour_density:.6f} "
                f"pos=({rect.x},{rect.y})"
            )


if __name__ == "__main__":
    main()
