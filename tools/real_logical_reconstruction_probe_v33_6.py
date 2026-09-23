from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from statistics import mean

from app.runtime.execution.vision.analyzers.visual_feature_extractor import (
    VisualFeatureExtractor,
)
from app.wh.vision.mss_screenshot_engine import MSSScreenshotEngine

from tools.real_logical_reconstruction_probe_v32 import (
    CAPTURE_DELAY_SECONDS,
    capture_groups,
)
from tools.real_logical_reconstruction_probe_v33_1 import (
    TemporalObject,
    build_temporal_objects,
)
from tools.real_logical_reconstruction_probe_v33_2 import (
    AggregatedVisualFeatures,
    VisualObjectProfile,
    build_profile,
)

TOP_RESULTS = 40


class QualityDecision(str, Enum):
    ACCEPT = "ACCEPT"
    UNCERTAIN = "UNCERTAIN"
    REJECT = "REJECT"


@dataclass(frozen=True, slots=True)
class QualityBreakdown:
    geometry_score: float
    structure_score: float
    overlap_score: float
    visual_score: float
    temporal_score: float
    quality_score: float
    decision: QualityDecision
    reasons: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class QualityProfile:
    object_id: str
    profile: VisualObjectProfile
    quality: QualityBreakdown


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def geometry_quality(
    profile: VisualObjectProfile,
) -> tuple[float, list[str]]:
    reasons: list[str] = []

    area_ratio = profile.area / float(1936 * 1168)

    if area_ratio > 0.12:
        area_score = 0.20
        reasons.append("large_screen_fraction")
    elif area_ratio > 0.06:
        area_score = 0.55
        reasons.append("elevated_screen_fraction")
    else:
        area_score = 1.0

    aspect = profile.aspect_ratio

    if aspect <= 3.0:
        aspect_score = 1.0
    elif aspect <= 6.0:
        aspect_score = 0.70
        reasons.append("wide_geometry")
    else:
        aspect_score = 0.35
        reasons.append("extreme_aspect_ratio")

    dimension_score = 1.0

    if profile.width <= 8 or profile.height <= 8:
        dimension_score = 0.35
        reasons.append("very_small_geometry")

    return (
        0.45 * area_score
        + 0.35 * aspect_score
        + 0.20 * dimension_score,
        reasons,
    )


def structure_quality(
    profile: VisualObjectProfile,
) -> tuple[float, list[str]]:
    reasons: list[str] = []

    member_count = profile.member_count
    mean_iou = profile.mean_member_iou
    max_iou = profile.max_member_iou
    member_area_ratio = profile.member_area_sum_ratio

    if member_count == 2:
        count_score = 1.0
    elif member_count == 3:
        count_score = 0.95
    elif member_count == 4:
        count_score = 0.80
    else:
        count_score = 0.35
        reasons.append("high_member_count")

    if mean_iou > 0.65:
        overlap_shape_score = 0.25
        reasons.append("high_mean_member_iou")
    elif mean_iou > 0.50:
        overlap_shape_score = 0.55
        reasons.append("elevated_mean_member_iou")
    else:
        overlap_shape_score = 1.0

    if max_iou > 0.85:
        max_overlap_score = 0.25
        reasons.append("near_duplicate_member_geometry")
    elif max_iou > 0.70:
        max_overlap_score = 0.60
        reasons.append("strong_member_overlap")
    else:
        max_overlap_score = 1.0

    if member_area_ratio > 2.20:
        area_structure_score = 0.25
        reasons.append("nested_area_pattern")
    elif member_area_ratio > 1.80:
        area_structure_score = 0.55
        reasons.append("elevated_member_area_sum")
    else:
        area_structure_score = 1.0

    score = (
        0.25 * count_score
        + 0.30 * overlap_shape_score
        + 0.20 * max_overlap_score
        + 0.25 * area_structure_score
    )

    return score, reasons


def overlap_quality(
    profile: VisualObjectProfile,
) -> tuple[float, list[str]]:
    reasons: list[str] = []

    if profile.pair_count == 0:
        return 0.20, ["no_member_pairs"]

    ratio = profile.overlap_pair_count / profile.pair_count

    if ratio >= 0.66:
        score = 1.0
    elif ratio >= 0.50:
        score = 0.80
    elif ratio >= 0.33:
        score = 0.55
        reasons.append("partial_member_overlap")
    else:
        score = 0.30
        reasons.append("weak_member_overlap")

    return score, reasons


def visual_quality(
    visual: AggregatedVisualFeatures,
) -> tuple[float, list[str]]:

    reasons: list[str] = []

    edge = visual.edge_density
    border = visual.border_edge_density
    interior = visual.interior_content_density
    horizontal = visual.horizontal_edge_density
    vertical = visual.vertical_edge_density

    score = 1.0

    if edge < 0.01:
        score -= 0.25
        reasons.append(
            f"very_low_edge_density={edge:.4f}"
        )

    if border < 0.001:
        score -= 0.15
        reasons.append(
            f"very_low_border_edge_density={border:.4f}"
        )

    if interior < 0.01:
        score -= 0.20
        reasons.append(
            f"very_low_interior_content_density={interior:.4f}"
        )

    if horizontal < 0.002 and vertical < 0.002:
        score -= 0.15
        reasons.append(
            "very_low_oriented_edge_density"
        )

    score = max(0.0, min(1.0, score))

    return score, reasons

def temporal_quality(
    temporal: TemporalObject,
) -> tuple[float, list[str]]:
    reasons: list[str] = []

    stability = temporal.stability

    if stability >= 0.90:
        score = 1.0
    elif stability >= 0.75:
        score = 0.80
    elif stability >= 0.60:
        score = 0.55
        reasons.append("moderate_temporal_stability")
    else:
        score = 0.25
        reasons.append("low_temporal_stability")

    if temporal.bbox_iou_12 < 0.50:
        reasons.append("bbox_instability_capture12")

    if temporal.bbox_iou_13 < 0.50:
        reasons.append("bbox_instability_capture13")

    return score, reasons


def classify_evidence(
    profile: VisualObjectProfile,
    reasons: tuple[str, ...],
) -> tuple[str, ...]:

    evidence: list[str] = []

    reason_set = set(reasons)

    aspect = profile.aspect_ratio
    width = profile.width
    height = profile.height
    member_count = profile.member_count
    max_iou = profile.max_member_iou

    #
    # HARD FAIL
    #
    # These combinations describe objects that are very likely
    # to be layout fragments rather than compact logical controls.
    #

    if (
        aspect > 12.0
        and width > 300
        and height < 60
    ):
        evidence.append(
            "HARD_FAIL:extreme_wide_layout_fragment"
        )

    if (
        aspect > 10.0
        and member_count >= 4
    ):
        evidence.append(
            "HARD_FAIL:extreme_geometry_with_many_members"
        )

    if (
        member_count >= 5
        and aspect > 8.0
    ):
        evidence.append(
            "HARD_FAIL:high_member_count_extreme_geometry"
        )

    #
    # UNCERTAIN
    #

    if "nested_area_pattern" in reason_set:
        evidence.append(
            "UNCERTAIN:nested_area_pattern"
        )

    if "strong_member_overlap" in reason_set:
        evidence.append(
            "UNCERTAIN:strong_member_overlap"
        )

    if "high_mean_member_iou" in reason_set:
        evidence.append(
            "UNCERTAIN:high_mean_member_iou"
        )

    if "elevated_member_area_sum" in reason_set:
        evidence.append(
            "UNCERTAIN:elevated_member_area_sum"
        )

    if (
        "extreme_aspect_ratio" in reason_set
        and not any(
            item.startswith("HARD_FAIL:")
            for item in evidence
        )
    ):
        evidence.append(
            "UNCERTAIN:extreme_aspect_ratio"
        )

    if "high_member_count" in reason_set:
        evidence.append(
            "UNCERTAIN:high_member_count"
        )

    #
    # POSITIVE EVIDENCE
    #

    if (
        member_count <= 3
        and max_iou < 0.70
        and "extreme_aspect_ratio" not in reason_set
    ):
        evidence.append(
            "POSITIVE:compact_structure"
        )

    if profile.stability >= 0.90:
        evidence.append(
            "POSITIVE:temporal_stability"
        )

    if (
        aspect <= 6.0
        and width < 300
        and height < 300
    ):
        evidence.append(
            "POSITIVE:reasonable_geometry"
        )

    return tuple(evidence)


def decide_quality(
    score: float,
    evidence: tuple[str, ...] = (),
) -> QualityDecision:
    hard_fail_count = sum(
        item.startswith("HARD_FAIL:")
        for item in evidence
    )

    uncertain_count = sum(
        item.startswith("UNCERTAIN:")
        for item in evidence
    )

    positive_count = sum(
        item.startswith("POSITIVE:")
        for item in evidence
    )

    # HARD REJECTION

    if hard_fail_count >= 1:
        return QualityDecision.REJECT

    if score < 0.50:
        return QualityDecision.REJECT

    # STRONG POSITIVE CASE

    if (
        score >= 0.90
        and positive_count >= 2
        and uncertain_count == 0
    ):
        return QualityDecision.ACCEPT

    # MULTIPLE WARNING SIGNALS

    if uncertain_count >= 2:
        if score >= 0.65:
            return QualityDecision.UNCERTAIN

        return QualityDecision.REJECT

    # SINGLE WARNING SIGNAL

    if uncertain_count == 1:
        if (
            score >= 0.90
            and positive_count >= 2
        ):
            return QualityDecision.ACCEPT

        if score >= 0.65:
            return QualityDecision.UNCERTAIN

        return QualityDecision.REJECT

    # SCORE-ONLY FALLBACK

    if score >= 0.75:
        return QualityDecision.ACCEPT

    if score >= 0.50:
        return QualityDecision.UNCERTAIN

    return QualityDecision.REJECT


def evaluate_profile(
    temporal: TemporalObject,
    profile: VisualObjectProfile,
) -> QualityProfile:
    geometry_score, geometry_reasons = geometry_quality(profile)
    structure_score, structure_reasons = structure_quality(profile)
    overlap_score, overlap_reasons = overlap_quality(profile)
    visual_score, visual_reasons = visual_quality(profile.visual)
    temporal_score, temporal_reasons = temporal_quality(temporal)

    quality_score = (
        0.20 * geometry_score
        + 0.25 * structure_score
        + 0.15 * overlap_score
        + 0.20 * visual_score
        + 0.20 * temporal_score
    )

    reasons = tuple(
        geometry_reasons
        + structure_reasons
        + overlap_reasons
        + visual_reasons
        + temporal_reasons
    )

    evidence = classify_evidence(profile, reasons)
    decision = decide_quality(quality_score, evidence)

    return QualityProfile(
        object_id=profile.object_id,
        profile=profile,
        quality=QualityBreakdown(
            geometry_score=geometry_score,
            structure_score=structure_score,
            overlap_score=overlap_score,
            visual_score=visual_score,
            temporal_score=temporal_score,
            quality_score=quality_score,
            decision=decision,
            reasons=reasons + evidence,
        ),
    )


def build_evidence_report(
    evaluated: list[QualityProfile],
) -> dict[str, dict[str, int]]:
    report = {
        "POSITIVE": {},
        "UNCERTAIN": {},
        "HARD_FAIL": {},
    }

    for item in evaluated:
        for evidence in item.quality.reasons:
            if ":" not in evidence:
                continue

            category, name = evidence.split(":", 1)

            if category not in report:
                continue

            report[category][name] = (
                report[category].get(name, 0) + 1
            )

    return report


def print_evidence_report(
    evaluated: list[QualityProfile],
) -> None:
    report = build_evidence_report(evaluated)

    print()
    print("-" * 100)
    print("EVIDENCE REPORT")
    print("-" * 100)

    for category in ("POSITIVE", "UNCERTAIN", "HARD_FAIL"):
        print()
        print(f"[{category}]")

        values = report[category]

        if not values:
            print("  none")
            continue

        for name, count in sorted(
            values.items(),
            key=lambda item: (-item[1], item[0]),
        ):
            print(f"  {name:<45} {count:>3}")

    decision_counts = {
        QualityDecision.ACCEPT: 0,
        QualityDecision.UNCERTAIN: 0,
        QualityDecision.REJECT: 0,
    }

    evidence_counts_per_decision = {
        QualityDecision.ACCEPT: 0,
        QualityDecision.UNCERTAIN: 0,
        QualityDecision.REJECT: 0,
    }

    for item in evaluated:
        decision = item.quality.decision
        decision_counts[decision] += 1

        evidence_counts_per_decision[decision] += sum(
            evidence.startswith(
                ("POSITIVE:", "UNCERTAIN:", "HARD_FAIL:")
            )
            for evidence in item.quality.reasons
        )

    print()
    print("-" * 100)
    print("DECISION / EVIDENCE SUMMARY")
    print("-" * 100)

    for decision in (
        QualityDecision.ACCEPT,
        QualityDecision.UNCERTAIN,
        QualityDecision.REJECT,
    ):
        count = decision_counts[decision]

        if count:
            average = (
                evidence_counts_per_decision[decision] / count
            )
        else:
            average = 0.0

        print(
            f"{decision.value:<12} "
            f"objects={count:>3}  "
            f"avg_evidence={average:.2f}"
        )


def print_object_evidence_report(
    evaluated: list[QualityProfile],
) -> None:
    print()
    print("-" * 100)
    print("OBJECT EVIDENCE")
    print("-" * 100)

    for item in evaluated[:TOP_RESULTS]:
        q = item.quality

        positive = [
            value
            for value in q.reasons
            if value.startswith("POSITIVE:")
        ]

        uncertain = [
            value
            for value in q.reasons
            if value.startswith("UNCERTAIN:")
        ]

        hard_fail = [
            value
            for value in q.reasons
            if value.startswith("HARD_FAIL:")
        ]

        print(
            f"{item.object_id} | "
            f"{q.decision.value:<10} | "
            f"score={q.quality_score:.3f}"
        )

        print(
            "  POSITIVE : "
            + (
                ", ".join(positive)
                if positive
                else "none"
            )
        )

        print(
            "  WARNING  : "
            + (
                ", ".join(uncertain)
                if uncertain
                else "none"
            )
        )

        print(
            "  HARD_FAIL: "
            + (
                ", ".join(hard_fail)
                if hard_fail
                else "none"
            )
        )


def capture_three_frames(window):
    engine = MSSScreenshotEngine()
    screenshots = []

    import time

    for _ in range(3):
        screenshots.append(engine.capture(window))
        time.sleep(CAPTURE_DELAY_SECONDS)

    return screenshots


def main() -> None:
    from app.runtime.execution.window.window_locator import WindowLocator

    locator = WindowLocator()
    window = locator.locate()

    if window is None:
        raise RuntimeError("WindowHub window not found.")

    print("=" * 100)
    print("V33.3 REAL LOGICAL RECONSTRUCTION — QUALITY GATE")
    print("=" * 100)
    print(f"WINDOW: {window}")
    print()

    screenshots = capture_three_frames(window)

    temporal_inputs = []

    for index in range(3):
        groups = capture_groups(index + 1, window)
        temporal_inputs.append(groups)

        print(
            f"CAPTURE {index + 1}: "
            f"groups={len(groups)}"
        )

    temporal_objects = build_temporal_objects(
        temporal_inputs[0],
        temporal_inputs[1],
        temporal_inputs[2],
    )

    extractor = VisualFeatureExtractor()

    profiles = [
        build_profile(
            temporal_object,
            screenshots,
            extractor,
        )
        for temporal_object in temporal_objects
    ]

    evaluated = [
        evaluate_profile(
            temporal_object,
            profile,
        )
        for temporal_object, profile in zip(
            temporal_objects,
            profiles,
            strict=True,
        )
    ]

    evaluated.sort(
        key=lambda item: item.quality.quality_score,
        reverse=True,
    )

    print()
    print("-" * 100)
    print_evidence_report(evaluated)
    print_object_evidence_report(evaluated)

    print("SUMMARY")
    print("-" * 100)

    decisions = {
        QualityDecision.ACCEPT: 0,
        QualityDecision.UNCERTAIN: 0,
        QualityDecision.REJECT: 0,
    }

    for item in evaluated:
        decisions[item.quality.decision] += 1

    print(f"TEMPORAL OBJECTS : {len(temporal_objects)}")
    print(f"ACCEPT            : {decisions[QualityDecision.ACCEPT]}")
    print(f"UNCERTAIN         : {decisions[QualityDecision.UNCERTAIN]}")
    print(f"REJECT            : {decisions[QualityDecision.REJECT]}")

    if evaluated:
        scores = [item.quality.quality_score for item in evaluated]

        print(f"QUALITY MIN       : {min(scores):.3f}")
        print(f"QUALITY MAX       : {max(scores):.3f}")
        print(f"QUALITY MEAN      : {mean(scores):.3f}")

    print()
    print("-" * 100)
    print("QUALITY TABLE")
    print("-" * 100)

    print(
        "OBJECT       DECISION     TOTAL   GEO     STRUCT  "
        "OVERLAP  VISUAL  TEMP    MEMBERS  BBOX"
    )

    for item in evaluated[:TOP_RESULTS]:
        p = item.profile
        q = item.quality

        print(
            f"{item.object_id:<12} "
            f"{q.decision.value:<12} "
            f"{q.quality_score:>5.3f}   "
            f"{q.geometry_score:>5.3f}   "
            f"{q.structure_score:>5.3f}   "
            f"{q.overlap_score:>5.3f}   "
            f"{q.visual_score:>5.3f}   "
            f"{q.temporal_score:>5.3f}   "
            f"{p.member_count:>3}      "
            f"({p.x},{p.y},{p.width},{p.height})"
        )

    print()
    print("-" * 100)
    print("DIAGNOSTICS")
    print("-" * 100)

    for item in evaluated[:TOP_RESULTS]:
        q = item.quality
        p = item.profile

        print(
            f"{item.object_id} | "
            f"{q.decision.value} | "
            f"score={q.quality_score:.3f} | "
            f"rect=({p.x},{p.y},{p.width},{p.height}) | "
            f"members={p.member_count} | "
            f"member_area_sum={p.member_area_sum_ratio:.3f} | "
            f"mean_iou={p.mean_member_iou:.3f} | "
            f"max_iou={p.max_member_iou:.3f}"
        )

        if q.reasons:
            print("  reasons: " + ", ".join(q.reasons))
        else:
            print("  reasons: none")

    print()
    print("=" * 100)
    print("V33.3 COMPLETE")
    print("=" * 100)


if __name__ == "__main__":
    main()


