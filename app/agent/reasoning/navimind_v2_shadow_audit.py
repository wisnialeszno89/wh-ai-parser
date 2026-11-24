"""Read-only comparison between NaviMind V2 proposals and V3 evidence policy.

Runs against the *existing* V2 capability inventory and model response. It
does not modify the V2 request/response, does not drive GUI actions, and must
not be used as a surrogate for local executor approval.

No model/customer text or WindowHub identifiers are included in diagnostics.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Mapping

from app.agent.reasoning.navimind_evidence_decision_engine import (
    ActionOption, DecisionContext, NextStep, plan_next_step,
    validate_model_proposal,
)


# Conservative protection: actions that may commit business changes are
# disallowed in V3, although V2's existing local policy remains authoritative.
_PERSISTENCE_TERMS = (
    "save", "send", "submit", "order", "persist", "delete",
    "zapisz", "zapis", "wyslij", "wyślij", "zamow", "zamów",
    "bestell", "speicher", "senden", "löschen", "loeschen",
)


@dataclass(frozen=True)
class ShadowAssessment:
    enabled: bool
    stage: str
    capability_count: int
    eligible_count: int
    model_decision: str
    v3_decision: str
    v3_reason: str
    proposal_decision: str
    proposal_reason: str
    # Deliberately no names, prices, labels, user input, ids or raw actions.
    disagreement: bool
    execution_affected: bool = False


def _persist_label(action: Mapping[str, Any]) -> bool:
    name = action.get("name")
    description = action.get("description")
    terms = " ".join(
        x.casefold() for x in (name, description) if isinstance(x, str)
    )
    return any(term in terms for term in _PERSISTENCE_TERMS)


def _option_key(name: str, ref: str | None) -> str:
    """Opaque model-to-inventory ID, used locally and never logged."""
    return "v2:" + sha256((name + "\0" + str(ref)).encode("utf-8")).hexdigest()[:20]


def _index_options(actions: object) -> tuple[tuple[ActionOption, ...], dict[tuple[str, str | None], str]]:
    if not isinstance(actions, list):
        return (), {}
    raw = []
    seen: dict[tuple[str, str | None], int] = {}
    for item in actions[:256]:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        ref = item.get("target_ref")
        if not isinstance(name, str) or not name.strip():
            continue
        if ref is not None and not isinstance(ref, str):
            continue
        fingerprint = (name, ref)
        seen[fingerprint] = seen.get(fingerprint, 0) + 1
        raw.append((item, name, ref, fingerprint))
    result: list[ActionOption] = []
    mapping: dict[tuple[str, str | None], str] = {}
    for item, name, ref, fingerprint in raw:
        key = _option_key(name, ref)
        # All "available" statuses here mean only *exposed by V2*.
        # Do not infer the UI control can be operated successfully.
        unique = seen[fingerprint] == 1 and ref is not None
        action = ActionOption(
            key=key,
            target="v2_local_capability",
            expected_result="requires_local_postcondition_readback",
            available=True,
            unique_target=unique,
            reversible=not _persist_label(item),
            requires_approval=bool(item.get("requires_confirmation")),
            persists_business_document=_persist_label(item),
            # No trusted catalogue/warranty source is inferred from UI.
        )
        result.append(action)
        if unique:
            mapping[fingerprint] = key
    return tuple(result), mapping


def assess_v2_shadow(
    *,
    stage: str,
    actions: object,
    response: Mapping[str, Any] | None,
    exact_document_verified: bool,
    observation_fresh: bool,
) -> ShadowAssessment:
    """Compare decisions after V2 model responds; never influence execution.

    This test-only/advisory operation cannot prove actual UI availability or
    completion. The existing V2 semantic action resolver and executor gates
    retain full authority. Unknown document identity is always conservative.
    """
    options, option_map = _index_options(actions)
    ctx = DecisionContext(
        goal="Assess currently exposed V2 capability inventory",
        stage=stage or "unknown",
        exact_document_verified=bool(exact_document_verified),
        observation_fresh=bool(observation_fresh),
        requested_result_verified=False,
        capabilities=options,
    )
    planned = plan_next_step(ctx)
    decision = response.get("decision") if isinstance(response, Mapping) else None
    model_decision = decision if isinstance(decision, str) else "unavailable"
    proposal_reason = "no_model_action_proposed"
    proposal_decision = "not_applicable"
    if model_decision == "act":
        action = response.get("action")
        name = action.get("name") if isinstance(action, Mapping) else None
        ref = action.get("target_ref") if isinstance(action, Mapping) else None
        fingerprint = (name, ref)
        key = option_map.get(fingerprint)
        if key is None:
            proposal_decision = NextStep.OBSERVE.value
            proposal_reason = "proposal_not_uniquely_exposed"
        else:
            result = validate_model_proposal(ctx, key)
            proposal_decision = result.kind.value
            proposal_reason = result.reason
    disagreement = (
        model_decision == "act" and proposal_decision != NextStep.ACT.value
        or model_decision == "done" and planned.kind != NextStep.COMPLETE
    )
    return ShadowAssessment(
        enabled=True,
        stage=stage or "unknown",
        capability_count=len(options),
        eligible_count=sum(
            x.available and x.unique_target and not x.persists_business_document
            and not x.requires_approval for x in options
        ),
        model_decision=model_decision,
        v3_decision=planned.kind.value,
        v3_reason=planned.reason,
        proposal_decision=proposal_decision,
        proposal_reason=proposal_reason,
        disagreement=disagreement,
    )


def shadow_diagnostics(result: ShadowAssessment) -> dict[str, object]:
    """Minimal, structured, customer-data-free stdout fields."""
    return {
        "NAVIMIND_SHADOW_ENABLED": result.enabled,
        "NAVIMIND_SHADOW_STAGE": result.stage,
        "NAVIMIND_SHADOW_CAPABILITIES": result.capability_count,
        "NAVIMIND_SHADOW_ELIGIBLE": result.eligible_count,
        "NAVIMIND_SHADOW_V3_DECISION": result.v3_decision,
        "NAVIMIND_SHADOW_MODEL_PROPOSAL": result.proposal_decision,
        "NAVIMIND_SHADOW_PROPOSAL_REASON": result.proposal_reason,
        "NAVIMIND_SHADOW_DISAGREEMENT": result.disagreement,
        "NAVIMIND_SHADOW_EXECUTION_AFFECTED": result.execution_affected,
    }
