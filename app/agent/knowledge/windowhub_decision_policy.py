"""Evidence-aware decisions for a salesperson-like WH Okna agent.

Pure, conservative policy; this module never drives Windows or trusts model
assertions as proof of UI state. The executor must supply fresh readback.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.agent.offers.windowhub_salesperson_policy import SalesPosition


class Decision(str, Enum):
    APPLY = "apply"
    KEEP = "keep"
    INSPECT = "inspect"
    SKIP_OPTIONAL = "skip_optional"
    PLACEHOLDER = "placeholder"
    ASK = "ask"
    STOP = "stop"
    SUBSTITUTE = "substitute"


@dataclass(frozen=True)
class FieldDecision:
    field: str
    action: Decision
    desired: str | None
    reason: str
    source: str
    requested: str | None = None
    substitution_requires_review: bool = False


@dataclass(frozen=True)
class FieldEvidence:
    """Fresh, externally measured properties of one exact field.

    available_options=None means the catalogue was not actually inspected;
    an empty tuple means it was inspected and offered no options.
    """
    observed: bool
    value: str | None = None
    available_options: tuple[str, ...] | None = None
    editable: bool = True
    unique_target: bool = True
    exact_document: bool = True


@dataclass(frozen=True)
class CatalogAlternative:
    label: str
    compatibility_verified: bool
    suitability_verified: bool
    deviation: str
    priority: int = 100


def choose_alternative(
    field: str,
    requested: str,
    candidates: tuple[CatalogAlternative, ...],
    *,
    same_document_verified: bool,
) -> FieldDecision:
    """Rank only options backed by actual compatibility and functional evidence."""
    if not same_document_verified:
        return FieldDecision(field, Decision.STOP, None,
                             "document_identity_unverified", "request", requested)
    valid = [c for c in candidates if c.compatibility_verified
             and c.suitability_verified and c.label.strip()]
    if not valid:
        return FieldDecision(field, Decision.ASK, None,
                             "no_verified_compatible_alternative", "request", requested)
    ordered = sorted(valid, key=lambda c: (c.priority, c.label.casefold()))
    if len(ordered) > 1 and ordered[0].priority == ordered[1].priority:
        return FieldDecision(field, Decision.ASK, None,
                             "equally_ranked_alternatives_need_review", "request", requested)
    choice = ordered[0]
    return FieldDecision(field, Decision.SUBSTITUTE, choice.label,
                         "verified_compatible_alternative:" + choice.deviation,
                         "catalogue_alternative", requested, True)


def decide_field(
    field: str,
    requested: str | None,
    evidence: FieldEvidence,
    *,
    default: str | None = None,
    required: bool = True,
    alternatives: tuple[CatalogAlternative, ...] = (),
) -> FieldDecision:
    """Choose a next step without silently replacing an explicit requirement.

    A value returned by this function is an *intent*, never a verified change.
    """
    user_requested = requested is not None and bool(requested.strip())
    desired = requested.strip() if user_requested else default
    source = "request" if user_requested else ("default" if default is not None else "unspecified")
    if not evidence.exact_document:
        return FieldDecision(field, Decision.STOP, desired, "document_identity_unverified", source)
    if not evidence.observed or not evidence.unique_target:
        return FieldDecision(field, Decision.INSPECT, desired, "fresh_unique_field_evidence_required", source)
    if desired is None:
        return FieldDecision(field, Decision.SKIP_OPTIONAL if not required else Decision.ASK,
                             None, "no_requested_value_or_approved_default", source)
    if evidence.value is not None and evidence.value.strip().casefold() == desired.casefold():
        return FieldDecision(field, Decision.KEEP, desired, "observed_value_matches", source)
    if evidence.available_options is not None:
        matches = [v for v in evidence.available_options if v.casefold() == desired.casefold()]
        if len(matches) != 1:
            if user_requested:
                alternative = choose_alternative(field, desired, alternatives,
                                                 same_document_verified=evidence.exact_document)
                if alternative.action == Decision.SUBSTITUTE:
                    if alternative.desired not in evidence.available_options:
                        return FieldDecision(field, Decision.INSPECT, desired,
                                             "alternative_not_in_live_catalogue", source)
                    return alternative
                return FieldDecision(field, Decision.ASK, desired,
                                     "requested_catalogue_value_unavailable_or_ambiguous", source)
            return FieldDecision(field, Decision.SKIP_OPTIONAL if not required else Decision.ASK,
                                 desired, "default_not_available_in_live_catalogue", source)
        desired = matches[0]
    if not evidence.editable:
        return FieldDecision(field, Decision.ASK if user_requested or required else Decision.SKIP_OPTIONAL,
                             desired, "field_read_only", source)
    return FieldDecision(field, Decision.APPLY, desired, "verify_after_action", source)


def decide_position_fallback(
    item: SalesPosition, *,
    dimensions_verified: bool,
    placeholder_supported: bool,
    unverified_or_unavailable: tuple[str, ...],
) -> Decision:
    """Do not misrepresent a technically incomplete position as a full offer."""
    if not unverified_or_unavailable:
        return Decision.INSPECT  # complete requires a separate construction readback
    if dimensions_verified and placeholder_supported:
        return Decision.PLACEHOLDER
    return Decision.ASK


def decision_context() -> dict[str, object]:
    """Compact reusable policy injected into the NaviMind V2 knowledge context."""
    return {
        "loop": ["observe", "identify_exact_document", "compare_request_with_live_values",
                 "choose_one_action", "validate_target", "execute_once", "readback", "update_progress"],
        "evidence": "Never infer success from dispatched clicks, old screenshots, OCR alone, or manual examples.",
        "catalogue": "A supplier catalogue is installation-specific; inspect live options. Never invent profile, glass or fitting compatibility.",
        "priority": "Explicit requirements outrank defaults; choose only technically verified compatible alternatives, and flag every substitution for salesperson review.",
        "defaults": {"both_sides_color": "biały only if neither side specified",
                     "glazing": "2 panes only if unspecified",
                     "discount": "0% only when no discount instruction exists",
                     "fittings": "UR ACTIVPILOT only for a compatible, verified tilt-turn catalogue choice"},
        "recovery": "On uncertain postcondition, reobserve before acting; never blind-retry a click or repeat position creation.",
        "partial": "If dimensions are verified and editor permits a blank position, preserve the draft and report missing requirements. Otherwise ask or stop.",
        "pricing": "Differentiate discount, markup and VAT; confirm only a fresh readback for the current document.",
        "approval": "Do not SAVE, send, submit, or convert an offer before salesperson review and explicit approval. Leave the draft unsaved and on screen.",
        "learning": "Keep provenance and regression tests for user corrections; do not promote a demonstration to an unconditional rule.",
        "substitution": "Choose only a live-available compatible and functionally suitable substitute; record requested versus chosen and deviation.",
        "review": "End with unsaved on-screen draft and report exact/alternative/default/partial fields and verification gaps.",
        "internet": "Public references are explanatory; dealer-specific catalogues and technical compatibility need live evidence.",
    }
