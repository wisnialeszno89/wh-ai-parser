from __future__ import annotations

import csv
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from app.runtime.execution.vision.analyzers.candidate_features import CandidateFeatureExtractor
from app.runtime.execution.vision.analyzers.candidate_filter import CandidateFilter
from app.runtime.execution.vision.analyzers.candidate_hierarchy import CandidateHierarchy
from app.runtime.execution.vision.analyzers.structural_classifier_v2 import StructuralClassifierV2
from app.runtime.execution.vision.analyzers.visual_feature_extractor import VisualFeatureExtractor


SCREENSHOT = Path("samples/wh_screen.png")
OUTPUT_IMAGE = Path("research/gui_lab/candidate_atlas.png")
OUTPUT_CSV = Path("research/gui_lab/candidate_atlas.csv")


def main() -> None:
    image = np.array(Image.open(SCREENSHOT).convert("RGB"))
    bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 60, 150)

    contours, hierarchy = cv2.findContours(
        edges,
        cv2.RETR_TREE,
        cv2.CHAIN_APPROX_SIMPLE,
    )

    candidate_filter = CandidateFilter()
    candidates = candidate_filter.filter(
        contours,
        hierarchy=hierarchy,
        roi_width=image.shape[1],
        roi_height=image.shape[0],
    )

    feature_extractor = CandidateFeatureExtractor(
        candidate_hierarchy=CandidateHierarchy()
    )
    features = feature_extractor.extract(
        candidates,
        roi_width=image.shape[1],
        roi_height=image.shape[0],
    )

    structural_classifier = StructuralClassifierV2()
    visual_extractor = VisualFeatureExtractor()

    structural_classifications = structural_classifier.classify(features)

    rows = []

    for index, (candidate, feature, structural) in enumerate(
        zip(candidates, features, structural_classifications),
        start=1,
    ):
        visual = visual_extractor.extract(
            bgr,
            candidate.rect,
            contours=contours,
        )

        rows.append(
            {
                "id": index,
                "contour_index": candidate.contour_index,
                "parent_contour_index": candidate.parent_contour_index,
                "x": candidate.rect.x,
                "y": candidate.rect.y,
                "width": candidate.rect.width,
                "height": candidate.rect.height,
                "area": feature.area,
                "aspect_ratio": round(feature.aspect_ratio, 6),
                "area_ratio": round(feature.area_ratio, 6),
                "width_ratio": round(feature.width_ratio, 6),
                "height_ratio": round(feature.height_ratio, 6),
                "center_x": round(feature.center_x, 6),
                "center_y": round(feature.center_y, 6),
                "depth": feature.depth,
                "children": feature.child_count,
                "siblings": feature.sibling_count,
                "edge_density": round(visual.edge_density, 6),
                "border_edge_density": round(visual.border_edge_density, 6),
                "horizontal_edge_density": round(visual.horizontal_edge_density, 6),
                "vertical_edge_density": round(visual.vertical_edge_density, 6),
                "contour_density": round(visual.contour_density, 6),
                "dark_pixel_ratio": round(visual.dark_pixel_ratio, 6),
                "bright_pixel_ratio": round(visual.bright_pixel_ratio, 6),
                "interior_content_density": round(visual.interior_content_density, 6),
                "structural_type": structural.control_type.name,
                "structural_confidence": round(structural.confidence, 6),
            }
        )

    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    annotated = Image.fromarray(image.copy())
    draw = ImageDraw.Draw(annotated)

    for row in rows:
        x = row["x"]
        y = row["y"]
        w = row["width"]
        h = row["height"]
        label = str(row["id"])

        draw.rectangle(
            [x, y, x + w, y + h],
            outline=(255, 0, 0),
            width=2,
        )

        label_x = x
        label_y = max(0, y - 14)

        draw.rectangle(
            [label_x, label_y, label_x + 24, label_y + 14],
            fill=(255, 0, 0),
        )
        draw.text(
            (label_x + 2, label_y),
            label,
            fill=(255, 255, 255),
        )

    annotated.save(OUTPUT_IMAGE)

    print(f"candidates: {len(rows)}")
    print(f"image: {OUTPUT_IMAGE}")
    print(f"csv:   {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
