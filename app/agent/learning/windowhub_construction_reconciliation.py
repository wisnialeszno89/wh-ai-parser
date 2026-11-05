"""Bridge semantic window construction plans to independently verified component IDs.

The legacy ConstructionStateObserver reports aggregate runtime history
(frame/sash/glass booleans), not per-element identities, counts or sides.
Never infer that one observed sash fulfills both left and right sashes.
This module is read-only and returns a gated proposed next step.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.window_model.dependency_planner import DependencyPlanner, ExecutableStep
from app.window_model.model import WindowElementType, WindowModel
from app.window_model.topology import infer_topology


@dataclass(frozen=True)
class ConstructionReconciliation:
    status: str
    next_step: ExecutableStep | None
    completed_ids: tuple[str, ...]
    remaining_ids: tuple[str, ...]
    reason: str


def reconcile_construction(
    desired: WindowModel,
    *,
    verified_element_ids=(),
) -> ConstructionReconciliation:
    """Only independently proved IDs may count as completed construction.

    An empty set produces the first proposal, but no GUI action is authorized.
    Every dependency is checked in the live/verified set, not merely in the
    theoretical order emitted by DependencyPlanner.
    """
    errors = desired.validate()
    if errors:
        raise ValueError("invalid_desired_window: " + "; ".join(errors))
    steps = DependencyPlanner().plan(desired, infer_topology(desired))
    ids = [step.element_id for step in steps]
    verified = tuple(verified_element_ids)
    if len(set(verified)) != len(verified):
        raise ValueError("duplicate_verified_element_id")
    if not set(verified).issubset(ids):
        raise ValueError("verified_elements_not_in_target_model")
    done = set(verified)
    remaining = tuple(i for i in ids if i not in done)
    if not remaining:
        return ConstructionReconciliation(
            "plan_fully_verified", None, verified, (), "all_expected_elements_individually_verified"
        )
    for step in steps:
        if step.element_id in done:
            continue
        required = (step.parent_id,) if step.parent_id and step.parent_id != desired.id else ()
        if all(dep in done for dep in required):
            return ConstructionReconciliation(
                "proposal_requires_live_verification",
                step, verified, remaining,
                "next_step_is_planned_only_not_executable_without_fresh_target_and_postcondition",
            )
    return ConstructionReconciliation(
        "blocked_by_unverified_dependencies", None, verified, remaining,
        "no_remaining_element_has_verified_parent",
    )


def reconcile_aggregate_observation(desired: WindowModel, observation) -> ConstructionReconciliation:
    """Conservatively inspect legacy aggregate state without claiming exact IDs.

    A boolean 'frame_present' or 'sash_present' may come from runtime history
    and cannot match distinct left/right components. No automatic skipping.
    """
    result = reconcile_construction(desired, verified_element_ids=())
    if any((
        getattr(observation, "frame_present", False),
        getattr(observation, "sash_present", False),
        getattr(observation, "glass_present", False),
        getattr(observation, "construction_present", False),
        getattr(observation, "runtime_history_present", False),
    )):
        return ConstructionReconciliation(
            "observation_insufficient_for_per_element_reconciliation",
            None, (), result.remaining_ids,
            "aggregate_runtime_signals_do_not_identify_each_planned_component",
        )
    if getattr(observation, "hardware_ready", False):
        return ConstructionReconciliation(
            "observation_insufficient_for_per_element_reconciliation",
            None, (), result.remaining_ids,
            "hardware_command_enabled_does_not_prove_hardware_is_installed",
        )
    return result


def two_sash_example() -> WindowModel:
    """Existing dependency-planner demo configuration, no invented catalogue."""
    model = WindowModel(properties={"width": 1460, "height": 1480})
    frame = model.add_element("frame", WindowElementType.FRAME)
    left = model.add_element("cell_left", WindowElementType.MULLION, parent_id=frame.id, role="CELL")
    right = model.add_element("cell_right", WindowElementType.MULLION, parent_id=frame.id, role="CELL")
    sash_left = model.add_element("sash_left", WindowElementType.SASH, parent_id=left.id, opening="left")
    sash_right = model.add_element("sash_right", WindowElementType.SASH, parent_id=right.id, opening="right")
    model.add_element("glass_left", WindowElementType.GLASS, parent_id=sash_left.id, panes=3)
    model.add_element("glass_right", WindowElementType.GLASS, parent_id=sash_right.id, panes=3)
    model.add_element("hardware_left", WindowElementType.HARDWARE, parent_id=sash_left.id, system="unknown")
    model.add_element("hardware_right", WindowElementType.HARDWARE, parent_id=sash_right.id, system="unknown")
    return model
