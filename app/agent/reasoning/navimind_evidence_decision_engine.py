"""NaviMind evidence-driven decision kernel (offline, no desktop access).

Separates knowledge gathering from action authority. This policy provides the
next *intent* only; the existing V2 executor remains the sole GUI authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class NextStep(str, Enum):
    ACT = "act"
    OBSERVE = "observe"
    CONSULT = "consult"
    ASK = "ask"
    STOP = "stop"
    COMPLETE = "complete"


class SourceKind(str, Enum):
    REQUEST = "request"
    LIVE_UI = "live_ui"
    WINKHAUS_DOC = "winkhaus_doc"
    LOCAL_RULE = "local_rule"
    PUBLIC_WEB = "public_web"
    MODEL_INFERENCE = "model_inference"
    HUMAN_CORRECTION = "human_correction"


@dataclass(frozen=True)
class KnowledgeFact:
    key: str
    value: str
    source: SourceKind
    reference: str
    applicable_to: str = "general"
    verified: bool = False


@dataclass(frozen=True)
class ActionOption:
    key: str
    target: str
    expected_result: str
    available: bool
    unique_target: bool
    reversible: bool = True
    requires_approval: bool = False
    persists_business_document: bool = False
    documentation_key: str | None = None
    requires_live_catalogue: bool = False


@dataclass(frozen=True)
class DecisionContext:
    goal: str
    stage: str
    exact_document_verified: bool
    observation_fresh: bool
    requested_result_verified: bool
    capabilities: tuple[ActionOption, ...] = ()
    knowledge: tuple[KnowledgeFact, ...] = ()
    pending_unknowns: tuple[str, ...] = ()
    attempted_without_progress: tuple[str, ...] = ()
    human_approval: bool = False


@dataclass(frozen=True)
class ReasonedStep:
    kind: NextStep
    action_key: str | None
    reason: str
    evidence_keys: tuple[str, ...] = ()
    unresolved: tuple[str, ...] = ()


def plan_next_step(ctx: DecisionContext) -> ReasonedStep:
    """Bounded and deterministic next-intent selector.

    Intentional hierarchy:
    1. Protect document identity and prevent unauthorized persistence.
    2. Observe first when the scene is stale.
    3. Finish only after independent business postcondition verification.
    4. Gather missing technical knowledge before high-risk selection.
    5. Choose only a uniquely observable eligible capability.
    6. Escalate genuine ambiguity or repeated non-progress.
    """
    if not ctx.goal.strip():
        raise ValueError("goal_required")
    if ctx.stage in ("order_document", "unknown", "windowhub_unmapped"):
        return ReasonedStep(NextStep.STOP, None, "unsupported_or_read_only_stage")
    if not ctx.exact_document_verified and ctx.stage != "start":
        return ReasonedStep(NextStep.OBSERVE, None, "document_identity_requires_observation")
    if not ctx.observation_fresh:
        return ReasonedStep(NextStep.OBSERVE, None, "fresh_scene_required")
    if ctx.requested_result_verified:
        return ReasonedStep(NextStep.COMPLETE, None, "independent_postcondition_verified")

    # Trusted source scope: manufacturer documentation can explain semantics,
    # but cannot substitute for options shown by the installed WindowHub.
    facts = {fact.key: fact for fact in ctx.knowledge
             if fact.verified and fact.source in (SourceKind.WINKHAUS_DOC, SourceKind.LOCAL_RULE, SourceKind.LIVE_UI)}
    missing = tuple(key for key in ctx.pending_unknowns if key not in facts)
    if missing:
        live_inspection_available = any(
            option.available and option.unique_target and option.key.startswith("inspect:")
            and not option.persists_business_document
            and (not option.requires_approval or ctx.human_approval)
            and option.key not in ctx.attempted_without_progress
            for option in ctx.capabilities
        )
        if live_inspection_available:
            inspect = next(o for o in ctx.capabilities
                           if o.available and o.unique_target and o.key.startswith("inspect:")
                           and not o.persists_business_document
                           and (not o.requires_approval or ctx.human_approval)
                           and o.key not in ctx.attempted_without_progress)
            return ReasonedStep(NextStep.ACT, inspect.key, "inspect_installed_catalogue_before_decision",
                                unresolved=missing)
        return ReasonedStep(NextStep.CONSULT, None, "retrieve_authorized_documentation_or_live_catalogue",
                            unresolved=missing)

    eligible = []
    blocked = []
    for option in ctx.capabilities:
        if not option.available or not option.unique_target:
            blocked.append(option.key)
            continue
        if option.key in ctx.attempted_without_progress:
            blocked.append(option.key)
            continue
        # No save/send/convert in autonomous draft. Human authorization to
        # proceed in the UI is not the same as approval to persist.
        if option.persists_business_document:
            blocked.append(option.key)
            continue
        if option.requires_approval and not ctx.human_approval:
            blocked.append(option.key)
            continue
        if option.requires_live_catalogue and not any(
            f.verified and f.source == SourceKind.LIVE_UI
            and f.key == "catalogue:" + option.key for f in ctx.knowledge
        ):
            blocked.append(option.key)
            continue
        if option.documentation_key is not None:
            doc = facts.get(option.documentation_key)
            if doc is None:
                blocked.append(option.key)
                continue
            # A public internet answer is never a substitute for a verified
            # installed-catalogue compatibility check.
            if doc.source not in (SourceKind.WINKHAUS_DOC, SourceKind.LOCAL_RULE, SourceKind.LIVE_UI):
                blocked.append(option.key)
                continue
        eligible.append(option)

    # Multiple possible UI actions are normal: avoid inventing a priority
    # from list order. The remote reasoner should disambiguate by goal/scene.
    if len(eligible) == 1:
        selected = eligible[0]
        return ReasonedStep(NextStep.ACT, selected.key, "unique_evidence_supported_action",
                            evidence_keys=((selected.documentation_key,)
                                           if selected.documentation_key else ()))
    if len(eligible) > 1:
        return ReasonedStep(NextStep.OBSERVE, None, "multiple_actions_require_goal_grounded_ranking",
                            unresolved=tuple(o.key for o in eligible))
    if any(option.persists_business_document for option in ctx.capabilities):
        return ReasonedStep(NextStep.ASK, None, "save_or_send_requires_separate_salesperson_review")
    if blocked:
        return ReasonedStep(NextStep.ASK, None, "no_safe_unique_action_after_recovery",
                            unresolved=tuple(blocked))
    return ReasonedStep(NextStep.CONSULT, None, "no_action_affordance_observed")


def validate_model_proposal(ctx: DecisionContext, proposed_action_key: str) -> ReasonedStep:
    """Validate one language-model suggestion against fresh, local evidence.

    The model ranks UI possibilities but cannot create new capabilities,
    override a blocked action, infer successful execution, or authorize
    persistent business changes. This is a *proposal*, not GUI execution.
    """
    if not isinstance(proposed_action_key, str) or not proposed_action_key:
        return ReasonedStep(NextStep.ASK, None, "missing_model_proposal")
    if ctx.requested_result_verified:
        return ReasonedStep(NextStep.COMPLETE, None, "independent_postcondition_verified")
    if ctx.stage in ("order_document", "unknown", "windowhub_unmapped"):
        return ReasonedStep(NextStep.STOP, None, "unsupported_or_read_only_stage")
    if not ctx.observation_fresh or (ctx.stage != "start" and not ctx.exact_document_verified):
        return ReasonedStep(NextStep.OBSERVE, None, "fresh_document_evidence_required")
    chosen = [o for o in ctx.capabilities if o.key == proposed_action_key]
    if len(chosen) != 1:
        return ReasonedStep(NextStep.OBSERVE, None, "model_target_not_uniquely_offered")
    option = chosen[0]
    if (not option.available or not option.unique_target
            or option.key in ctx.attempted_without_progress):
        return ReasonedStep(NextStep.OBSERVE, None, "model_target_stale_ambiguous_or_repeated")
    if option.persists_business_document:
        return ReasonedStep(NextStep.ASK, None, "save_or_send_requires_separate_salesperson_review")
    if option.requires_approval and not ctx.human_approval:
        return ReasonedStep(NextStep.ASK, None, "explicit_approval_required")

    facts = {
        f.key: f for f in ctx.knowledge
        if f.verified and f.source in (
            SourceKind.WINKHAUS_DOC, SourceKind.LOCAL_RULE, SourceKind.LIVE_UI,
        )
    }
    missing = tuple(key for key in ctx.pending_unknowns if key not in facts)
    # Allow explicit inspection to resolve missing information, not editing.
    if missing and not proposed_action_key.startswith("inspect:"):
        return ReasonedStep(NextStep.CONSULT, None, "missing_evidence_before_model_action", unresolved=missing)
    if option.requires_live_catalogue and not any(
        f.verified and f.source == SourceKind.LIVE_UI
        and f.key == "catalogue:" + option.key for f in ctx.knowledge
    ):
        return ReasonedStep(NextStep.CONSULT, None, "installed_catalogue_verification_required",
                            unresolved=("catalogue:" + option.key,))
    if option.documentation_key is not None and option.documentation_key not in facts:
        return ReasonedStep(NextStep.CONSULT, None, "proposed_action_lacks_verified_rule",
                            unresolved=(option.documentation_key,))
    return ReasonedStep(
        NextStep.ACT, option.key, "model_proposal_validated_against_local_evidence",
        evidence_keys=((option.documentation_key,) if option.documentation_key else ()),
        unresolved=missing,
    )
