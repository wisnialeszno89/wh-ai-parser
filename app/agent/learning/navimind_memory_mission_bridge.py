"""Read-only persistent-learning preflight for NaviMind quotation missions.

Builds a *new* immutable task tuple from a pinned, verified offer. Active
approved textual rules are applied only to matching request descriptions.
Never edits documents, changes prices, authorizes business persistence or
turns learned text into verified product/manufacturer knowledge.

The result's tasks must be used consistently by both planner and readback.
The UI executor remains the existing validated V2 execution boundary.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

from app.agent.learning.navimind_correction_rulebook import LearningScope
from app.agent.learning.navimind_versioned_rule_memory import RuleMemoryStore
from app.agent.runtime.navimind_mission_coordinator import (
    MissionScene, PositionTask,
)


@dataclass(frozen=True)
class AppliedLearning:
    position_id: str
    rule_id: str
    source_generation: int
    original_text: str
    suggested_text: str
    scope: LearningScope


@dataclass(frozen=True)
class PreparedMission:
    tasks: tuple[PositionTask, ...]
    memory_generation: int
    applied: tuple[AppliedLearning, ...]
    # The learned descriptions are draft suggestions, not claims of UI writes.
    desktop_actions_performed: bool = False
    save_authorized: bool = False
    send_authorized: bool = False
    production_approved: bool = False


def prepare_mission_with_memory(
    store: RuleMemoryStore, tasks: tuple[PositionTask, ...],
    scene: MissionScene, *,
    workflow: str = "commercial_quote",
    context_tags: dict[str, tuple[str, ...]] | None = None,
) -> PreparedMission:
    """Consult one consistent snapshot before planning the next mission.

    No rule is used when the exact WindowHub document is unverified or the
    observation is stale. For repeatability, the caller must retain the
    returned tasks throughout one mission, rather than reloading memory
    mid-action. A later revision is a NEW mission replan, never a silent edit.
    """
    if not tasks or len({t.position_id for t in tasks}) != len(tasks):
        raise ValueError("nonempty_unique_positions_required")
    if not workflow.strip():
        raise ValueError("workflow_required")
    if not (
        scene.application == "WindowHub"
        and scene.document_identity_verified
        and scene.fresh
        and scene.document_id
    ):
        raise ValueError("verified_exact_document_required_before_memory_use")
    tag_lookup = context_tags or {}
    if set(tag_lookup) - {task.position_id for task in tasks}:
        raise ValueError("unknown_position_context")
    saved = store.load()  # Fail closed on corrupt, unsupported or conflicting memory.
    updated: list[PositionTask] = []
    changes: list[AppliedLearning] = []
    for task in tasks:
        tags = tag_lookup.get(task.position_id, ())
        if not isinstance(tags, tuple) or not all(isinstance(tag, str) for tag in tags):
            raise ValueError("invalid_position_context")
        scope = LearningScope(scene.application, workflow, "description", tags)
        match = saved.book.suggest(scope, task.request.description)
        if match is None:
            updated.append(task)
            continue
        rule_id, suggested = match
        if suggested == task.request.description:
            updated.append(task)
            continue
        # Copy only literal description; request dimensions, imagery, customer
        # requirements, monetary fields and technical findings never change.
        updated.append(replace(task, request=replace(task.request, description=suggested)))
        changes.append(AppliedLearning(
            task.position_id, rule_id, saved.generation,
            task.request.description, suggested, scope,
        ))
    return PreparedMission(
        tasks=tuple(updated), memory_generation=saved.generation,
        applied=tuple(changes),
    )


def verify_memory_generation_unchanged(
    store: RuleMemoryStore, prepared: PreparedMission,
) -> bool:
    """Call before dispatching a planned edit after external activity.

    If a rule was revoked or memory changed, callers must stop and replan;
    a stale proposal must never bypass the normal human takeover epoch gate.
    """
    return store.load().generation == prepared.memory_generation
