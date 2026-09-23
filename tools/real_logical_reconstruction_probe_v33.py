from __future__ import annotations

from dataclasses import dataclass
from math import hypot

import cv2

from app.runtime.execution.window.window_locator import WindowLocator
from app.wh.vision.mss_screenshot_engine import MSSScreenshotEngine

from tools.real_logical_reconstruction_probe_v32 import (
    calculate_stability,
    capture_groups,
)


TOP_PROFILES = 50
MIN_STABLE = True


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
    group_id: str
    x: int
    y: int
    width: int
    height: int

    member_count: int
    stability: float

    aspect_ratio: float
    area: int

    edge_density: float
    border_edge_density: float
    horizontal_edge_density: float
    vertical_edge_density: float
    contour_density: float

    dark_pixel_ratio: float
    bright_pixel_ratio: float
    interior_content_density: float

    member_area_ratio: float
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
    ax = a.x
    ay = a.y
    aw = a.width
    ah = a.height

    bx = b.x
    by = b.y
    bw = b.width
    bh = b.height

    left = max(ax, bx)
    top = max(ay, by)
    right = min(ax + aw, bx + bw)
    bottom = min(ay + ah, by + bh)

    width = max(0, right - left)
    height = max(0, bottom - top)

    intersection = width * height

    if intersection <= 0:
        return 0.0

    union = aw * ah + bw * bh - intersection

    if union <= 0:
        return 0.0

    return intersection / union


def calculate_visual_features(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    if gray.size == 0:
        return (
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
        )

    edges = cv2.Canny(gray, 60, 150)

    edge_density = float((edges > 0).mean())

    h, w = gray.shape

    border_mask = cv2.copyMakeBorder(
        cv2.inRange(gray, 0, 255),
        1,
        1,
        1,
        1,
        cv2.BORDER_CONSTANT,
        value=0,
    )

    border_pixels = (
        gray[0, :].size
        + gray[-1, :].size
        + gray[:, 0].size
        + gray[:, -1].size
    )

    border_edges = (
        (edges[0, :] > 0).sum()
        + (edges[-1, :] > 0).sum()
        + (edges[:, 0] > 0).sum()
        + (edges[:, -1] > 0).sum()
    )

    border_edge_density = (
        float(border_edges / border_pixels)
        if border_pixels
        else 0.0
    )

    horizontal_kernel = cv2.Sobel(
        gray,
        cv2.CV_64F,
        1,
        0,
        ksize=3,
    )

    vertical_kernel = cv2.Sobel(
        gray,
        cv2.CV_64F,
        0,
        1,
        ksize=3,
    )

    horizontal_edge_density = float(
        (abs(horizontal_kernel) > 40).mean()
    )

    vertical_edge_density = float(
        (abs(vertical_kernel) > 40).mean()
    )

    contours, _ = cv2.findContours(
        edges,
        cv2.RETR_LIST,
        cv2.CHAIN_APPROX_SIMPLE,
    )

    contour_density = (
        len(contours) / float(max(1, w * h))
    )

    dark_pixel_ratio = float((gray < 70).mean())
    bright_pixel_ratio = float((gray > 190).mean())

    if h >= 4 and w >= 4:
        interior = gray[2:-2, 2:-2]
        interior_edges = edges[2:-2, 2:-2]
        interior_content_density = float(
            (interior_edges > 0).mean()
        )
    else:
        interior_content_density = edge_density

    return (
        edge_density,
        border_edge_density,
        horizontal_edge_density,
        vertical_edge_density,
        contour_density,
        dark_pixel_ratio,
        bright_pixel_ratio,
        interior_content_density,
    )


def build_profile(
    group,
    screenshot,
    stability: float,
) -> VisualObjectProfile:

    image = screenshot.image

    x = max(0, group.x)
    y = max(0, group.y)

    right = min(
        image.shape[1],
        group.x + group.width,
    )

    bottom = min(
        image.shape[0],
        group.y + group.height,
    )

    crop = image[y:bottom, x:right]

    (
        edge_density,
        border_edge_density,
        horizontal_edge_density,
        vertical_edge_density,
        contour_density,
        dark_pixel_ratio,
        bright_pixel_ratio,
        interior_content_density,
    ) = calculate_visual_features(crop)

    members = tuple(group.members)

    member_profiles = []

    for member in members:
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

        member_profiles.append(
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

    widths = [member.width for member in members]
    heights = [member.height for member in members]

    width_mean = (
        sum(widths) / len(widths)
        if widths
        else 0.0
    )

    height_mean = (
        sum(heights) / len(heights)
        if heights
        else 0.0
    )

    width_std = (
        (
            sum(
                (value - width_mean) ** 2
                for value in widths
            )
            / len(widths)
        ) ** 0.5
        if widths
        else 0.0
    )

    height_std = (
        (
            sum(
                (value - height_mean) ** 2
                for value in heights
            )
            / len(heights)
        ) ** 0.5
        if heights
        else 0.0
    )

    total_member_area = sum(
        member.width * member.height
        for member in members
    )

    member_area_ratio = (
        total_member_area
        / float(max(1, group.width * group.height))
    )

    ious = []

    for index, member_a in enumerate(members):
        for member_b in members[index + 1:]:
            ious.append(rect_iou(member_a, member_b))

    overlap_ious = [
        value
        for value in ious
        if value > 0.0
    ]

    return VisualObjectProfile(
        group_id=group.group_id,
        x=group.x,
        y=group.y,
        width=group.width,
        height=group.height,
        member_count=len(members),
        stability=stability,
        aspect_ratio=(
            group.width / group.height
            if group.height
            else 0.0
        ),
        area=group.width * group.height,
        edge_density=edge_density,
        border_edge_density=border_edge_density,
        horizontal_edge_density=horizontal_edge_density,
        vertical_edge_density=vertical_edge_density,
        contour_density=contour_density,
        dark_pixel_ratio=dark_pixel_ratio,
        bright_pixel_ratio=bright_pixel_ratio,
        interior_content_density=interior_content_density,
        member_area_ratio=member_area_ratio,
        member_width_mean=width_mean,
        member_height_mean=height_mean,
        member_width_std=width_std,
        member_height_std=height_std,
        pair_count=len(ious),
        overlap_pair_count=len(overlap_ious),
        mean_member_iou=(
            sum(ious) / len(ious)
            if ious
            else 0.0
        ),
        max_member_iou=max(ious, default=0.0),
        members=tuple(member_profiles),
    )


def print_profile(profile: VisualObjectProfile) -> None:
    print()
    print(
        f"PROFILE {profile.group_id} "
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
        f"  visual: "
        f"edge={profile.edge_density:.4f} "
        f"border={profile.border_edge_density:.4f} "
        f"h={profile.horizontal_edge_density:.4f} "
        f"v={profile.vertical_edge_density:.4f}"
    )

    print(
        f"  pixels: "
        f"dark={profile.dark_pixel_ratio:.4f} "
        f"bright={profile.bright_pixel_ratio:.4f} "
        f"interior={profile.interior_content_density:.4f}"
    )

    print(
        f"  structure: "
        f"member_area={profile.member_area_ratio:.4f} "
        f"member_w={profile.member_width_mean:.2f}"
        f"+/-{profile.member_width_std:.2f} "
        f"member_h={profile.member_height_mean:.2f}"
        f"+/-{profile.member_height_std:.2f}"
    )

    print(
        f"  overlap: "
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
    print("REAL LOGICAL RECONSTRUCTION PROBE V33")
    print("STABLE VISUAL OBJECT PROFILING")
    print("=" * 100)

    window = WindowLocator().locate()

    print(
        f"WINDOW: "
        f"({window.left},{window.top}) "
        f"{window.width}x{window.height}"
    )

    # V32 stability pass.
    all_groups = []

    for capture_index in range(1, 4):
        groups = capture_groups(
            capture_index,
            window,
        )
        all_groups.extend(groups)

    all_groups = tuple(all_groups)

    stability_results = calculate_stability(
        all_groups
    )

    stable_results = [
        result
        for result in stability_results
        if result.stable
    ]

    print()
    print(
        f"V32 stable bases: "
        f"{len(stable_results)}"
    )

    if not stable_results:
        print("NO STABLE GROUPS")
        return

    # Fresh screenshot used only for visual profiling.
    screenshot = MSSScreenshotEngine().capture(
        window
    )

    profiles = []

    for result in stable_results:
        base = result.capture_groups[0].group

        profile = build_profile(
            base,
            screenshot,
            result.stability_score,
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
    print("V33 SUMMARY")
    print("=" * 100)

    print(
        f"STABLE OBJECT PROFILES: "
        f"{len(profiles)}"
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

    for profile in profiles[:TOP_PROFILES]:
        print_profile(profile)

    print()
    print("=" * 100)
    print("V33 COMPLETE")
    print("=" * 100)


if __name__ == "__main__":
    main()
