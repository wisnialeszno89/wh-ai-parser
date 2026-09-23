from __future__ import annotations

from dataclasses import dataclass
from statistics import mean


from app.runtime.execution.window.window_locator import WindowLocator
from app.wh.vision.mss_screenshot_engine import MSSScreenshotEngine

from tools.real_logical_reconstruction_probe_v32 import (
    GROUP_MATCH_IOU,
    MEMBER_MATCH_IOU,
    MAX_BBOX_SHIFT,
    MAX_SIZE_DELTA,
    GroupHypothesis,
    capture_groups,
    match_groups,
)


@dataclass(frozen=True, slots=True)
class TemporalObject:
    object_id: str
    base_group: GroupHypothesis
    capture2_group: GroupHypothesis
    capture3_group: GroupHypothesis
    bbox_iou_12: float
    bbox_iou_13: float
    member_ratio_12: float
    member_ratio_13: float
    shift_12: float
    shift_13: float

    @property
    def stability(self) -> float:
        presence = 1.0
        bbox_score = mean((self.bbox_iou_12, self.bbox_iou_13))
        member_score = mean((self.member_ratio_12, self.member_ratio_13))
        shift_score = max(
            0.0,
            1.0 - mean((self.shift_12, self.shift_13)) / MAX_BBOX_SHIFT,
        )

        return (
            0.35 * presence
            + 0.30 * bbox_score
            + 0.25 * member_score
            + 0.10 * shift_score
        )


def best_match(
    base,
    candidates,
    used_ids: set[str],
):
    matches = []

    for candidate in candidates:
        candidate_group = candidate.group

        if candidate_group.group_id in used_ids:
            continue

        result = match_groups(
            base,
            candidate,
        )

        if result is None:
            continue

        bbox_iou = result.bbox_iou
        shift = result.bbox_shift
        size_delta = result.size_delta
        member_ratio = result.member_match_ratio

        matches.append(
            (
                candidate,
                bbox_iou,
                member_ratio,
                shift,
                size_delta,
            )
        )

    if not matches:
        return None

    matches.sort(
        key=lambda item: (
            item[1],
            item[2],
            -item[3],
            -item[4],
        ),
        reverse=True,
    )

    candidate, bbox_iou, member_ratio, shift, _ = matches[0]

    return (
        candidate,
        bbox_iou,
        member_ratio,
        shift,
    )


def calculate_member_match_ratio(
    first: GroupHypothesis,
    second: GroupHypothesis,
) -> float:
    if not first.members or not second.members:
        return 0.0

    matched = 0

    for member_a in first.members:
        best_iou = 0.0

        for member_b in second.members:
            best_iou = max(
                best_iou,
                rect_iou(
                    member_a.rect,
                    member_b.rect,
                ),
            )

        if best_iou >= MEMBER_MATCH_IOU:
            matched += 1

    denominator = max(
        len(first.members),
        len(second.members),
    )

    return matched / denominator


def rect_iou(
    first: tuple[int, int, int, int],
    second: tuple[int, int, int, int],
) -> float:
    ax, ay, aw, ah = first
    bx, by, bw, bh = second

    left = max(ax, bx)
    top = max(ay, by)
    right = min(ax + aw, bx + bw)
    bottom = min(ay + ah, by + bh)

    intersection_width = max(0, right - left)
    intersection_height = max(0, bottom - top)

    intersection = intersection_width * intersection_height

    if intersection <= 0:
        return 0.0

    area_a = aw * ah
    area_b = bw * bh

    union = area_a + area_b - intersection

    if union <= 0:
        return 0.0

    return intersection / union


def build_temporal_objects(
    capture1,
    capture2,
    capture3,
) -> list[TemporalObject]:
    used_capture2: set[str] = set()
    used_capture3: set[str] = set()

    temporal_objects: list[TemporalObject] = []

    for base_capture in capture1:
        match2 = best_match(
            base_capture,
            capture2,
            used_capture2,
        )

        if match2 is None:
            continue

        capture2_group, bbox_iou_12, member_ratio_12, shift_12 = match2

        match3 = best_match(
            base_capture,
            capture3,
            used_capture3,
        )

        if match3 is None:
            continue

        capture3_group, bbox_iou_13, member_ratio_13, shift_13 = match3

        base = base_capture.group
        group2 = capture2_group.group
        group3 = capture3_group.group

        used_capture2.add(group2.group_id)
        used_capture3.add(group3.group_id)

        temporal_objects.append(
            TemporalObject(
                object_id=f"TO-{len(temporal_objects) + 1:03d}",
                base_group=base,
                capture2_group=group2,
                capture3_group=group3,
                bbox_iou_12=bbox_iou_12,
                bbox_iou_13=bbox_iou_13,
                member_ratio_12=member_ratio_12,
                member_ratio_13=member_ratio_13,
                shift_12=shift_12,
                shift_13=shift_13,
            )
        )

    return temporal_objects


def print_temporal_object(obj: TemporalObject) -> None:
    group = obj.base_group

    print(
        f"{obj.object_id} "
        f"bbox=({group.x},{group.y},{group.width},{group.height}) "
        f"members={len(group.members)} "
        f"stability={obj.stability:.3f}"
    )

    print(
        f"  C1→C2: "
        f"bbox_iou={obj.bbox_iou_12:.3f} "
        f"member_ratio={obj.member_ratio_12:.3f} "
        f"shift={obj.shift_12:.1f}"
    )

    print(
        f"  C1→C3: "
        f"bbox_iou={obj.bbox_iou_13:.3f} "
        f"member_ratio={obj.member_ratio_13:.3f} "
        f"shift={obj.shift_13:.1f}"
    )


def main() -> None:
    print("=== V33.1 TEMPORAL VISUAL OBJECT IDENTITY ===")

    locator = WindowLocator()
    window = locator.locate()

    print(
        f"WindowHub: "
        f"{window.left},{window.top} "
        f"{window.width}x{window.height}"
    )

    screenshot_engine = MSSScreenshotEngine()

    captures = []

    for index in range(3):
        screenshot = screenshot_engine.capture(window)

        groups = capture_groups(
            screenshot,
            window,
        )

        captures.append(groups)

        print(
            f"CAPTURE {index + 1}: "
            f"GROUPS={len(groups)}"
        )

        if index < 2:
            import time
            time.sleep(0.35)

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

    print(
        f"C1 GROUPS: {len(capture1)}"
    )
    print(
        f"C2 GROUPS: {len(capture2)}"
    )
    print(
        f"C3 GROUPS: {len(capture3)}"
    )

    if temporal_objects:
        print()
        print("=== TEMPORAL OBJECTS ===")

        for obj in temporal_objects:
            print_temporal_object(obj)

    print()
    print("=== SUMMARY ===")

    if temporal_objects:
        stabilities = [
            obj.stability
            for obj in temporal_objects
        ]

        member_counts = [
            len(obj.base_group.members)
            for obj in temporal_objects
        ]

        print(
            f"STABILITY MIN/MAX/MEAN: "
            f"{min(stabilities):.3f} / "
            f"{max(stabilities):.3f} / "
            f"{mean(stabilities):.3f}"
        )

        print(
            "MEMBER COUNT DISTRIBUTION:"
        )

        for count in sorted(set(member_counts)):
            print(
                f"  {count}: "
                f"{member_counts.count(count)}"
            )

    print()
    print("V33.1 COMPLETE")


if __name__ == "__main__":
    main()





