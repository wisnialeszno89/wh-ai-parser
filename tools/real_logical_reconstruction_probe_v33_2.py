from __future__ import annotations

from dataclasses import dataclass
from statistics import mean, pstdev
from time import sleep

from app.runtime.execution.window.window_locator import WindowLocator
from app.runtime.execution.vision.analyzers.visual_feature_extractor import (
    VisualFeatureExtractor,
)
from app.runtime.execution.vision.models.rect import Rect
from app.wh.vision.mss_screenshot_engine import MSSScreenshotEngine

from tools.real_logical_reconstruction_probe_v32 import (
    CAPTURE_DELAY_SECONDS,
    capture_groups,
)

from tools.real_logical_reconstruction_probe_v33_1 import (
    TemporalObject,
    build_temporal_objects,
)


TOP_PROFILES = 50


@dataclass(frozen=True, slots=True)
class AggregatedVisualFeatures:
    edge_density: float
    border_edge_density: float
    horizontal_edge_density: float
    vertical_edge_density: float
    contour_density: float
    dark_pixel_ratio: float
    bright_pixel_ratio: float
    interior_content_density: float

    edge_density_std: float
    border_edge_density_std: float
    horizontal_edge_density_std: float
    vertical_edge_density_std: float
    contour_density_std: float
    dark_pixel_ratio_std: float
    bright_pixel_ratio_std: float
    interior_content_density_std: float


@dataclass(frozen=True, slots=True)
class MemberProfile:
    contour_index: int
    parent_contour_index: int | None
    x: int
    y: int
    width: int
    height: int
    depth: int

    relative_x: float
    relative_y: float
    relative_width: float
    relative_height: float


@dataclass(frozen=True, slots=True)
class VisualObjectProfile:
    object_id: str

    x: int
    y: int
    width: int
    height: int

    member_count: int
    stability: float

    aspect_ratio: float
    area: int

    visual: AggregatedVisualFeatures

    member_area_sum_ratio: float
    member_width_mean: float
    member_height_mean: float
    member_width_std: float
    member_height_std: float

    pair_count: int
    overlap_pair_count: int
    mean_member_iou: float
    max_member_iou: float

    members: tuple[MemberProfile, ...]


def rect_iou(a, b) -> float:
    left = max(a.x, b.x)
    top = max(a.y, b.y)
    right = min(a.x + a.width, b.x + b.width)
    bottom = min(a.y + a.height, b.y + b.height)

    intersection_width = max(0, right - left)
    intersection_height = max(0, bottom - top)
    intersection = intersection_width * intersection_height

    if intersection <= 0:
        return 0.0

    union = (
        a.width * a.height
        + b.width * b.height
        - intersection
    )

    if union <= 0:
        return 0.0

    return intersection / union


def group_rect(group) -> Rect:
    return Rect(
        x=group.x,
        y=group.y,
        width=group.width,
        height=group.height,
    )


def extract_features(
    extractor: VisualFeatureExtractor,
    screenshot,
    group,
):
    rect = group_rect(group)

    return extractor.extract(
        screenshot.image,
        rect,
    )


def aggregate_features(feature_sets) -> AggregatedVisualFeatures:
    def values(name: str):
        return [getattr(features, name) for features in feature_sets]

    def avg(name: str) -> float:
        data = values(name)
        return mean(data) if data else 0.0

    def std(name: str) -> float:
        data = values(name)
        return pstdev(data) if len(data) > 1 else 0.0

    return AggregatedVisualFeatures(
        edge_density=avg("edge_density"),
        border_edge_density=avg("border_edge_density"),
        horizontal_edge_density=avg("horizontal_edge_density"),
        vertical_edge_density=avg("vertical_edge_density"),
        contour_density=avg("contour_density"),
        dark_pixel_ratio=avg("dark_pixel_ratio"),
        bright_pixel_ratio=avg("bright_pixel_ratio"),
        interior_content_density=avg("interior_content_density"),

        edge_density_std=std("edge_density"),
        border_edge_density_std=std("border_edge_density"),
        horizontal_edge_density_std=std("horizontal_edge_density"),
        vertical_edge_density_std=std("vertical_edge_density"),
        contour_density_std=std("contour_density"),
        dark_pixel_ratio_std=std("dark_pixel_ratio"),
        bright_pixel_ratio_std=std("bright_pixel_ratio"),
        interior_content_density_std=std("interior_content_density"),
    )


def build_member_profiles(group) -> tuple[MemberProfile, ...]:
    result = []

    for member in group.members:
        relative_x = (
            (member.x - group.x) / group.width
            if group.width
            else 0.0
        )

        relative_y = (
            (member.y - group.y) / group.height
            if group.height
            else 0.0
        )

        relative_width = (
            member.width / group.width
            if group.width
            else 0.0
        )

        relative_height = (
            member.height / group.height
            if group.height
            else 0.0
        )

        result.append(
            MemberProfile(
                contour_index=member.contour_index,
                parent_contour_index=member.parent_contour_index,
                x=member.x,
                y=member.y,
                width=member.width,
                height=member.height,
                depth=member.depth,
                relative_x=relative_x,
                relative_y=relative_y,
                relative_width=relative_width,
                relative_height=relative_height,
            )
        )

    return tuple(result)


def build_profile(
    temporal_object: TemporalObject,
    screenshots,
    extractor: VisualFeatureExtractor,
) -> VisualObjectProfile:
    groups = (
        temporal_object.base_group,
        temporal_object.capture2_group,
        temporal_object.capture3_group,
    )

    feature_sets = [
        extract_features(
            extractor,
            screenshot,
            group,
        )
        for screenshot, group in zip(screenshots, groups)
    ]

    visual = aggregate_features(feature_sets)

    base = temporal_object.base_group
    members = tuple(base.members)

    widths = [member.width for member in members]
    heights = [member.height for member in members]

    width_mean = mean(widths) if widths else 0.0
    height_mean = mean(heights) if heights else 0.0

    width_std = pstdev(widths) if len(widths) > 1 else 0.0
    height_std = pstdev(heights) if len(heights) > 1 else 0.0

    total_member_area = sum(
        member.width * member.height
        for member in members
    )

    group_area = max(1, base.width * base.height)

    member_area_sum_ratio = (
        total_member_area / float(group_area)
    )

    ious = []

    for index, member_a in enumerate(members):
        for member_b in members[index + 1:]:
            ious.append(
                rect_iou(member_a, member_b)
            )

    overlap_ious = [
        value
        for value in ious
        if value > 0.0
    ]

    return VisualObjectProfile(
        object_id=temporal_object.object_id,

        x=base.x,
        y=base.y,
        width=base.width,
        height=base.height,

        member_count=len(members),
        stability=temporal_object.stability,

        aspect_ratio=(
            base.width / base.height
            if base.height
            else 0.0
        ),

        area=base.width * base.height,

        visual=visual,

        member_area_sum_ratio=member_area_sum_ratio,

        member_width_mean=width_mean,
        member_height_mean=height_mean,
        member_width_std=width_std,
        member_height_std=height_std,

        pair_count=len(ious),
        overlap_pair_count=len(overlap_ious),

        mean_member_iou=(
            mean(ious)
            if ious
            else 0.0
        ),

        max_member_iou=max(ious, default=0.0),

        members=build_member_profiles(base),
    )


def print_profile(profile: VisualObjectProfile) -> None:
    visual = profile.visual

    print()
    print(
        f"PROFILE {profile.object_id} "
        f"bounds=({profile.x},{profile.y},"
        f"{profile.width},{profile.height})"
    )

    print(
        f"  stability={profile.stability:.3f} "
        f"members={profile.member_count} "
        f"aspect={profile.aspect_ratio:.3f} "
        f"area={profile.area}"
    )

    print(
        "  visual: "
        f"edge={visual.edge_density:.4f} "
        f"border={visual.border_edge_density:.4f} "
        f"h={visual.horizontal_edge_density:.4f} "
        f"v={visual.vertical_edge_density:.4f}"
    )

    print(
        "  pixels: "
        f"dark={visual.dark_pixel_ratio:.4f} "
        f"bright={visual.bright_pixel_ratio:.4f} "
        f"interior={visual.interior_content_density:.4f}"
    )

    print(
        "  visual_std: "
        f"edge={visual.edge_density_std:.5f} "
        f"border={visual.border_edge_density_std:.5f} "
        f"h={visual.horizontal_edge_density_std:.5f} "
        f"v={visual.vertical_edge_density_std:.5f}"
    )

    print(
        "  structure: "
        f"member_area_sum={profile.member_area_sum_ratio:.4f} "
        f"member_w={profile.member_width_mean:.2f}"
        f"+/-{profile.member_width_std:.2f} "
        f"member_h={profile.member_height_mean:.2f}"
        f"+/-{profile.member_height_std:.2f}"
    )

    print(
        "  overlap: "
        f"pairs={profile.pair_count} "
        f"overlap_pairs={profile.overlap_pair_count} "
        f"mean_iou={profile.mean_member_iou:.4f} "
        f"max_iou={profile.max_member_iou:.4f}"
    )

    for member in profile.members:
        print(
            f"    MEMBER contour={member.contour_index} "
            f"parent={member.parent_contour_index} "
            f"depth={member.depth} "
            f"rect=({member.x},{member.y},"
            f"{member.width},{member.height}) "
            f"rel=("
            f"{member.relative_x:.3f},"
            f"{member.relative_y:.3f},"
            f"{member.relative_width:.3f},"
            f"{member.relative_height:.3f})"
        )


def main() -> None:
    print("=" * 100)
    print("REAL LOGICAL RECONSTRUCTION PROBE V33.2")
    print("STABLE VISUAL OBJECT PROFILES")
    print("PRODUCTION VISUAL FEATURE EXTRACTOR")
    print("=" * 100)

    window = WindowLocator().locate()

    print(
        f"WINDOW: "
        f"({window.left},{window.top}) "
        f"{window.width}x{window.height}"
    )

    screenshot_engine = MSSScreenshotEngine()
    extractor = VisualFeatureExtractor()

    captures = []
    screenshots = []

    for index in range(3):
        screenshot = screenshot_engine.capture(window)

        groups = capture_groups(
            index + 1,
            window,
        )

        screenshots.append(screenshot)
        captures.append(groups)

        print(
            f"CAPTURE {index + 1}: "
            f"groups={len(groups)}"
        )

        if index < 2:
            sleep(CAPTURE_DELAY_SECONDS)

    capture1, capture2, capture3 = captures

    temporal_objects = build_temporal_objects(
        capture1,
        capture2,
        capture3,
    )

    print()
    print(
        f"TEMPORAL OBJECTS: "
        f"{len(temporal_objects)}"
    )

    profiles = []

    for temporal_object in temporal_objects:
        profile = build_profile(
            temporal_object,
            screenshots,
            extractor,
        )

        profiles.append(profile)

    profiles.sort(
        key=lambda profile: (
            -profile.stability,
            -profile.member_count,
            -profile.area,
        )
    )

    print()
    print("=" * 100)
    print("V33.2 SUMMARY")
    print("=" * 100)

    print(
        f"STABLE VISUAL OBJECT PROFILES: "
        f"{len(profiles)}"
    )

    if profiles:
        stabilities = [
            profile.stability
            for profile in profiles
        ]

        print(
            f"STABILITY MIN/MAX/MEAN: "
            f"{min(stabilities):.3f} / "
            f"{max(stabilities):.3f} / "
            f"{mean(stabilities):.3f}"
        )

        member_counts = {}

        for profile in profiles:
            member_counts[profile.member_count] = (
                member_counts.get(
                    profile.member_count,
                    0,
                ) + 1
            )

        print(
            "MEMBER COUNT DISTRIBUTION: "
            + ", ".join(
                f"{count}={total}"
                for count, total
                in sorted(member_counts.items())
            )
        )

    print()
    print(
        "SOURCE OF VISUAL FEATURES: "
        "app.runtime.execution.vision.analyzers."
        "visual_feature_extractor.VisualFeatureExtractor"
    )

    print()

    for profile in profiles[:TOP_PROFILES]:
        print_profile(profile)

    print()
    print("=" * 100)
    print("V33.2 COMPLETE")
    print("=" * 100)


if __name__ == "__main__":
    main()
